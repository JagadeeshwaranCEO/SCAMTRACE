"""Local whisper.cpp command-line adapter.

No model is downloaded or contacted during inference.  The model binary must
already be present in models/ so core processing remains available offline.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from backend.config import settings
from backend.utils.transcript import normalize_security_terms


class LocalWhisperEngine:
    def __init__(self) -> None:
        self.model_path = settings.asr_model
        self.binary = self._find_binary()

    def _find_binary(self) -> str | None:
        candidates = [settings.whisper_cpp_bin, "whisper-cli", "main"]
        for candidate in candidates:
            if candidate and (Path(candidate).exists() or shutil.which(candidate)):
                return candidate
        return None

    def status(self) -> dict[str, Any]:
        available = bool(self.binary and self.model_path.exists())
        message = "Ready for local transcription." if available else (
            "Local ASR is not installed. Use ./scripts/setup_models.py once while online, "
            "then audio transcription runs without network access."
        )
        return {
            "engine": "whisper.cpp",
            "available": available,
            "binary": self.binary or "not found",
            "model": str(self.model_path),
            "model_available": self.model_path.exists(),
            "message": message,
        }

    def transcribe(self, audio_path: Path, language: str = "auto") -> dict[str, Any]:
        status = self.status()
        if not status["available"]:
            raise RuntimeError(status["message"])
        with tempfile.TemporaryDirectory(prefix="scamtrace_asr_") as temp_dir:
            temp = Path(temp_dir)
            wav_path = temp / "input.wav"
            self._convert_to_wav(audio_path, wav_path)
            output_prefix = temp / "transcript"
            command = [
                str(self.binary), "-m", str(self.model_path), "-f", str(wav_path),
                "-oj", "-of", str(output_prefix), "-ng",
            ]
            if language != "auto":
                command.extend(["-l", {"hinglish": "hi", "ta": "ta", "hi": "hi", "en": "en"}.get(language, language)])
            result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=False)
            if result.returncode != 0:
                error = (result.stderr or result.stdout).strip()[-1000:]
                raise RuntimeError(f"Local ASR failed: {error}")
            json_path = output_prefix.with_suffix(".json")
            if json_path.exists():
                return self._parse_json(json_path)
            return self._parse_stdout(result.stdout, language)

    def _convert_to_wav(self, input_path: Path, output_path: Path) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if input_path.suffix.lower() == ".wav":
            shutil.copy2(input_path, output_path)
            return
        if not ffmpeg:
            raise RuntimeError("ffmpeg is required to transcribe this audio format.")
        result = subprocess.run(
            [ffmpeg, "-y", "-i", str(input_path), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(output_path)],
            capture_output=True, text=True, timeout=60, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("Could not decode the audio file.")

    def _parse_json(self, source: Path) -> dict[str, Any]:
        raw = json.loads(source.read_text(encoding="utf-8"))
        transcription = raw.get("transcription") or raw.get("result", {}).get("transcription") or raw.get("segments") or []
        segments = []
        for item in transcription:
            stamps = item.get("timestamps", {})
            offsets = item.get("offsets", {})
            start = offsets.get("from", item.get("start", 0)) / (1000 if offsets else 1)
            end = offsets.get("to", item.get("end", 0)) / (1000 if offsets else 1)
            segments.append({"start": round(float(start), 2), "end": round(float(end), 2), "text": item.get("text", "").strip()})
        raw_text = " ".join(item["text"] for item in segments).strip()
        text, corrections = normalize_security_terms(raw_text)
        if not text:
            raise RuntimeError("ASR returned no speech. Try clearer audio or another language.")
        language = raw.get("result", {}).get("language", raw.get("language", "auto"))
        return {
            "text": text, "raw_text": raw_text, "corrections": corrections,
            "language": language, "segments": segments, "engine": "whisper.cpp",
        }

    def _parse_stdout(self, output: str, language: str) -> dict[str, Any]:
        segments = []
        for line in output.splitlines():
            match = re.match(r"\s*\[(\d\d):(\d\d):(\d\d\.\d+)\s*-->\s*(\d\d):(\d\d):(\d\d\.\d+)\]\s*(.+)", line)
            if match:
                start = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))
                end = int(match.group(4)) * 3600 + int(match.group(5)) * 60 + float(match.group(6))
                segments.append({"start": start, "end": end, "text": match.group(7).strip()})
        raw_text = " ".join(item["text"] for item in segments).strip()
        text, corrections = normalize_security_terms(raw_text)
        if not text:
            raise RuntimeError("ASR output could not be parsed.")
        return {
            "text": text, "raw_text": raw_text, "corrections": corrections,
            "language": language, "segments": segments, "engine": "whisper.cpp",
        }
