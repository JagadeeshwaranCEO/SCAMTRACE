"""Hardened local HTTP server for the SCAMTRACE dashboard."""

from __future__ import annotations

import json
import mimetypes
import re
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from backend.config import settings
from backend.service import ScamTraceService
from backend.utils.logging import logger


SERVICE = ScamTraceService()
STATIC_ROOT = settings.root / "static"


class ScamTraceHandler(BaseHTTPRequestHandler):
    server_version = "SCAMTRACE/0.4"
    protocol_version = "HTTP/1.1"

    def log_message(self, message: str, *args: object) -> None:
        logger.info(json.dumps({"event": "http", "message": message % args}))

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; media-src 'self' blob:;")
        super().end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/status":
            return self._json(HTTPStatus.OK, SERVICE.status())
        realtime_match = re.fullmatch(r"/api/realtime/session/([0-9a-f]{32})", path)
        if realtime_match:
            return self._json(HTTPStatus.OK, SERVICE.realtime.snapshot(realtime_match.group(1)))
        if path in {"/", "/index.html"}:
            return self._static("index.html")
        if path.startswith("/static/"):
            return self._static(path.removeprefix("/static/"))
        self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._body_json()
            if path == "/api/analyze/text":
                output = SERVICE.analyze_text(payload.get("text", ""), payload.get("language", "auto"))
            elif path == "/api/analyze/scenario":
                output = SERVICE.analyze_scenario(str(payload.get("scenario_id", "")))
            elif path == "/api/analyze/audio":
                output = SERVICE.analyze_audio(
                    payload.get("audio_base64", ""), payload.get("filename", "recording.wav"), payload.get("language", "auto")
                )
            elif path == "/api/report":
                output = SERVICE.report(payload.get("result", {}), payload.get("include_sensitive_evidence") is True)
            elif path == "/api/feedback":
                output = SERVICE.record_feedback(
                    str(payload.get("analysis_id", "")),
                    str(payload.get("outcome", "")),
                    str(payload.get("language", "auto")),
                    str(payload.get("threat_level", "")),
                    payload.get("threat_score"),
                )
            elif path == "/api/realtime/session":
                output = SERVICE.realtime.start(str(payload.get("language", "auto")))
            else:
                realtime_match = re.fullmatch(r"/api/realtime/session/([0-9a-f]{32})/(segment|close)", path)
                if not realtime_match:
                    return self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                session_id, action = realtime_match.groups()
                if action == "segment":
                    output = SERVICE.realtime.ingest(
                        session_id,
                        payload.get("text", ""),
                        payload.get("start"),
                        payload.get("end"),
                        payload.get("language"),
                    )
                else:
                    output = SERVICE.realtime.close(session_id)
            self._json(HTTPStatus.OK, output)
        except (ValueError, RuntimeError) as exc:
            logger.info(json.dumps({"event": "request_rejected", "reason": str(exc)}))
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception:
            logger.exception("Unhandled API error")
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Internal processing error. Check local logs."})

    def _body_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        max_json = settings.max_upload_bytes * 2
        if content_length <= 0:
            raise ValueError("Request body is required.")
        if content_length > max_json:
            raise ValueError("Request exceeds the allowed size.")
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            raise ValueError("Only JSON requests are accepted.")
        raw = self.rfile.read(content_length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid JSON request.") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON request must be an object.")
        return payload

    def _json(self, status: HTTPStatus, payload: dict) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _static(self, requested: str) -> None:
        if not re.fullmatch(r"[a-zA-Z0-9._/-]+", requested):
            return self._json(HTTPStatus.BAD_REQUEST, {"error": "Invalid path"})
        path = (STATIC_ROOT / requested).resolve()
        if STATIC_ROOT.resolve() not in path.parents and path != STATIC_ROOT.resolve():
            return self._json(HTTPStatus.FORBIDDEN, {"error": "Forbidden"})
        if not path.is_file():
            return self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
        content = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") else content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    startup = SERVICE.status()
    print("SCAMTRACE startup check")
    print(f"- Language classifier: {'ready' if startup['classifier']['available'] else startup['classifier']['warning']}")
    print(f"- Local ASR: {startup['asr']['message']}")
    print(f"- Voice signal: {startup['voice_auth']['mode']}")
    try:
        server = ThreadingHTTPServer((settings.host, settings.port), ScamTraceHandler)
    except OSError as exc:
        print(f"SCAMTRACE could not start on {settings.host}:{settings.port}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print(f"SCAMTRACE is running locally at http://{settings.host}:{settings.port}")
    print("Privacy mode: raw audio is processed in a temporary local directory and is not persisted.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSCAMTRACE stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
