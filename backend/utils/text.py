"""Text handling and basic Indian-language identification."""

from __future__ import annotations

import re
from typing import Any


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def detect_language(text: str, requested: str = "auto") -> str:
    if requested and requested != "auto":
        return requested
    if re.search(r"[\u0B80-\u0BFF]", text):
        return "ta"
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    hinglish_markers = ("aapka", "jaldi", "paisa", "kripya", "karo", "mat karo", "aadhaar")
    return "hinglish" if any(marker in normalize_text(text) for marker in hinglish_markers) else "en"


def text_segments(text: str, seconds_per_segment: float = 6.0) -> list[dict[str, Any]]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?।])\s+|\n+", text) if s.strip()]
    if not sentences and text.strip():
        sentences = [text.strip()]
    return [
        {
            "start": round(index * seconds_per_segment, 2),
            "end": round((index + 1) * seconds_per_segment, 2),
            "text": sentence,
        }
        for index, sentence in enumerate(sentences)
    ]

