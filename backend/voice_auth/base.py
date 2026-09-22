"""Voice-authentication protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, TypedDict


class VoiceResult(TypedDict, total=False):
    synthetic_score: float
    label: str
    confidence: float
    model: str
    available: bool
    features: dict[str, float]
    warning: str


class VoiceAuthenticator(Protocol):
    def analyze(self, audio_path: Path) -> VoiceResult: ...

