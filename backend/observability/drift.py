"""Aggregate-only novelty monitoring for the local language baseline.

This is deliberately not telemetry. It never receives or stores a transcript,
audio sample, phrase, identifier, or model feature. It only helps the local
operator notice when the current traffic differs from the model's known
feature coverage. Retraining always requires a separate, consented dataset.
"""

from __future__ import annotations

import threading
from collections import Counter, deque
from typing import Any


class LocalDriftMonitor:
    """Keep a bounded, process-local aggregate of feature-coverage signals."""

    def __init__(self, max_observations: int = 128) -> None:
        self._max_observations = max_observations
        self._values: deque[dict[str, Any]] = deque(maxlen=max_observations)
        self._lock = threading.RLock()

    def observe(self, classifier: dict[str, Any], language: str, tactics: list[dict[str, Any]]) -> dict[str, Any]:
        """Return one content-free novelty observation and update local aggregate."""
        coverage = classifier.get("feature_coverage", {})
        known_ratio = _bounded_float(coverage.get("known_word_phrase_ratio", 0.0))
        unknown_ratio = round(1.0 - known_ratio, 4)
        observation = {
            "mode": "LOCAL_EPHEMERAL_AGGREGATE_ONLY",
            "persistence": "OFF",
            "raw_content_retained": "NO",
            "known_word_phrase_ratio": known_ratio,
            "unknown_word_phrase_ratio": unknown_ratio,
            "novelty": _novelty_label(known_ratio),
            "language": _safe_language(language),
            "tactic_count": min(12, max(0, len(tactics))),
            "note": "Feature coverage is a drift cue, not a scam signal and does not change the alert.",
        }
        with self._lock:
            self._values.append({
                "known_word_phrase_ratio": known_ratio,
                "language": observation["language"],
                "tactic_count": observation["tactic_count"],
            })
            observation["window"] = self._window_summary_locked()
        return observation

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "available": True,
                "mode": "LOCAL_EPHEMERAL_AGGREGATE_ONLY",
                "persistence": "OFF",
                "raw_content_retained": "NO",
                "purpose": "Model-coverage review; never changes a live alert or trains a model automatically.",
                "window": self._window_summary_locked(),
            }

    def _window_summary_locked(self) -> dict[str, Any]:
        if not self._values:
            return {"observations": 0, "state": "INSUFFICIENT_LOCAL_OBSERVATIONS"}
        count = len(self._values)
        mean_known = sum(item["known_word_phrase_ratio"] for item in self._values) / count
        languages = Counter(item["language"] for item in self._values)
        state = "REVIEW_NOVELTY" if count >= 12 and mean_known < 0.14 else "OBSERVING"
        return {
            "observations": count,
            "mean_known_word_phrase_ratio": round(mean_known, 4),
            "languages": dict(sorted(languages.items())),
            "state": state,
        }


def _bounded_float(value: object) -> float:
    try:
        return round(min(1.0, max(0.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _safe_language(value: object) -> str:
    language = str(value or "auto").lower()
    return language if language in {"auto", "en", "hi", "ta", "hinglish"} else "other"


def _novelty_label(known_ratio: float) -> str:
    if known_ratio < 0.08:
        return "HIGH_NOVELTY"
    if known_ratio < 0.22:
        return "MODERATE_NOVELTY"
    return "EXPECTED_COVERAGE"
