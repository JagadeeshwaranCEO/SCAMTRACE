"""Speech-recognition protocol and result types."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class ASREngine(Protocol):
    def status(self) -> dict[str, Any]: ...
    def transcribe(self, audio_path: Path, language: str = "auto") -> dict[str, Any]: ...

