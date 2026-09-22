"""Configuration loaded from environment without external dependencies."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Load a local .env file without adding a runtime dependency."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_dotenv()


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    return value in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8765"))
    debug: bool = _bool("DEBUG", False)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    asr_model: Path = ROOT / os.getenv("ASR_MODEL", "models/ggml-base.bin")
    whisper_cpp_bin: str = os.getenv("WHISPER_CPP_BIN", "")
    enable_voice_auth: bool = _bool("ENABLE_VOICE_AUTH", True)
    enable_narrative_protocol: bool = _bool("ENABLE_NARRATIVE_PROTOCOL", True)
    enable_drift_monitor: bool = _bool("ENABLE_DRIFT_MONITOR", True)
    enable_feedback: bool = _bool("ENABLE_FEEDBACK", True)
    enable_mic: bool = _bool("ENABLE_MIC", True)
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "auto")
    realtime_max_sessions: int = int(os.getenv("REALTIME_MAX_SESSIONS", "32"))
    realtime_session_ttl_seconds: int = int(os.getenv("REALTIME_SESSION_TTL_SECONDS", "900"))
    realtime_max_segments: int = int(os.getenv("REALTIME_MAX_SEGMENTS", "500"))

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()
