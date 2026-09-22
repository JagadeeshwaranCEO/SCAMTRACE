"""In-memory incremental analysis sessions.

This layer is intentionally transport-agnostic: a phone client, a local ASR
worker, or the demo CLI can feed timestamped transcript segments as they arrive.
No raw audio or transcript is written to disk by this module.
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from typing import Any


class RealtimeSessionManager:
    """Maintain bounded, short-lived analysis sessions in local process memory."""

    def __init__(
        self,
        analyze: Callable[..., dict[str, Any]],
        max_sessions: int = 32,
        ttl_seconds: int = 900,
        max_segments: int = 500,
    ) -> None:
        self._analyze = analyze
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds
        self.max_segments = max_segments
        self._sessions: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def start(self, language: str = "auto") -> dict[str, Any]:
        with self._lock:
            self._prune()
            if len(self._sessions) >= self.max_sessions:
                raise RuntimeError("Realtime session capacity reached. Close an inactive session and retry.")
            session_id = os.urandom(16).hex()
            now = time.monotonic()
            self._sessions[session_id] = {
                "language": language or "auto",
                "created_at": now,
                "updated_at": now,
                "segments": [],
                "sequence": 0,
            }
            return {
                "session_id": session_id,
                "mode": "LOCAL_EPHEMERAL_INCREMENTAL_ANALYSIS",
                "expires_in_seconds": self.ttl_seconds,
                "persistence": "OFF",
            }

    def ingest(
        self,
        session_id: str,
        text: str,
        start: float | None = None,
        end: float | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        clean_text = str(text).strip()
        if not clean_text:
            raise ValueError("A non-empty transcript segment is required.")
        if len(clean_text) > 10_000:
            raise ValueError("Transcript segment exceeds the 10,000 character safety limit.")
        with self._lock:
            self._prune()
            session = self._get(session_id)
            if len(session["segments"]) >= self.max_segments:
                raise RuntimeError("Realtime session segment limit reached. Start a new session.")
            previous_end = float(session["segments"][-1]["end"]) if session["segments"] else 0.0
            segment_start = max(previous_end, float(start)) if start is not None else previous_end
            segment_end = max(segment_start + 0.1, float(end)) if end is not None else segment_start + 3.0
            segment = {"start": round(segment_start, 2), "end": round(segment_end, 2), "text": clean_text}
            session["segments"].append(segment)
            session["sequence"] += 1
            session["updated_at"] = time.monotonic()
            transcript = " ".join(item["text"] for item in session["segments"])
            active_language = language or session["language"]
            result = self._analyze(
                transcript,
                active_language,
                list(session["segments"]),
                source="REALTIME_INCREMENTAL",
            )
            result["realtime"] = {
                "session_id": session_id,
                "sequence": session["sequence"],
                "accepted_segment": segment,
                "mode": "LOCAL_EPHEMERAL_INCREMENTAL_ANALYSIS",
                "persistence": "OFF",
                "alert": result["fusion"]["level"] in {"HIGH", "CRITICAL"},
            }
            return result

    def snapshot(self, session_id: str) -> dict[str, Any]:
        with self._lock:
            self._prune()
            session = self._get(session_id)
            return {
                "session_id": session_id,
                "language": session["language"],
                "segment_count": len(session["segments"]),
                "last_timestamp": session["segments"][-1]["end"] if session["segments"] else 0.0,
                "expires_in_seconds": max(0, round(self.ttl_seconds - (time.monotonic() - session["updated_at"]))),
                "persistence": "OFF",
            }

    def close(self, session_id: str) -> dict[str, Any]:
        with self._lock:
            self._prune()
            session = self._get(session_id)
            summary = {
                "session_id": session_id,
                "closed": True,
                "segments_analyzed": len(session["segments"]),
                "persistence": "OFF",
            }
            del self._sessions[session_id]
            return summary

    def _get(self, session_id: str) -> dict[str, Any]:
        if not isinstance(session_id, str) or len(session_id) != 32 or any(char not in "0123456789abcdef" for char in session_id):
            raise ValueError("Invalid realtime session identifier.")
        try:
            return self._sessions[session_id]
        except KeyError as exc:
            raise ValueError("Realtime session not found or expired.") from exc

    def _prune(self) -> None:
        cutoff = time.monotonic() - self.ttl_seconds
        expired = [key for key, value in self._sessions.items() if value["updated_at"] < cutoff]
        for key in expired:
            del self._sessions[key]
