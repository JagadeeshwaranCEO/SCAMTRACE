"""Explicit, content-free local feedback records.

Feedback records model-decision outcomes only. They intentionally exclude
transcripts, audio, evidence phrases, caller IDs, and free-text notes. This is
useful for calibration review without silently building a surveillance corpus.
"""

from __future__ import annotations

import os
import re
import threading
from collections import Counter, deque
from typing import Any


OUTCOMES = {"CONFIRMED_SCAM", "FALSE_ALERT", "MISSED_SCAM", "UNSURE"}
LEVELS = {"LOW", "VERIFY", "HIGH", "CRITICAL"}
ANALYSIS_ID = re.compile(r"[0-9a-f]{16}")


class LocalFeedbackRegistry:
    """Retain only a short-lived, process-local feedback aggregate."""

    def __init__(self, max_records: int = 128) -> None:
        self._records: deque[dict[str, Any]] = deque(maxlen=max_records)
        self._lock = threading.RLock()

    def record(self, analysis_id: str, outcome: str, language: str, threat_level: str, threat_score: object) -> dict[str, Any]:
        if not ANALYSIS_ID.fullmatch(str(analysis_id)):
            raise ValueError("Invalid analysis identifier for feedback.")
        normalized_outcome = str(outcome).upper()
        if normalized_outcome not in OUTCOMES:
            raise ValueError("Feedback outcome must be CONFIRMED_SCAM, FALSE_ALERT, MISSED_SCAM, or UNSURE.")
        normalized_level = str(threat_level).upper()
        if normalized_level not in LEVELS:
            raise ValueError("Feedback threat level is invalid.")
        try:
            score = min(100, max(0, int(round(float(threat_score)))))
        except (TypeError, ValueError) as exc:
            raise ValueError("Feedback threat score is invalid.") from exc
        record = {
            "outcome": normalized_outcome,
            "language": _safe_language(language),
            "threat_level": normalized_level,
            "threat_score_band": f"{score // 10 * 10}-{min(100, score // 10 * 10 + 9)}",
        }
        with self._lock:
            self._records.append(record)
            summary = self._summary_locked()
        return {
            "accepted": True,
            "feedback_id": os.urandom(8).hex(),
            "storage": "LOCAL MEMORY ONLY — cleared when SCAMTRACE stops",
            "raw_content_retained": "NO",
            "automatic_retraining": "NO",
            "summary": summary,
        }

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "available": True,
                "mode": "EXPLICIT_USER_CONFIRMATION",
                "storage": "LOCAL MEMORY ONLY",
                "raw_content_retained": "NO",
                "automatic_retraining": "NO",
                "summary": self._summary_locked(),
            }

    def _summary_locked(self) -> dict[str, Any]:
        return {
            "records": len(self._records),
            "outcomes": dict(sorted(Counter(item["outcome"] for item in self._records).items())),
        }


def _safe_language(value: object) -> str:
    language = str(value or "auto").lower()
    return language if language in {"auto", "en", "hi", "ta", "hinglish"} else "other"
