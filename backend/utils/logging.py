"""Structured, local-only application logging."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from backend.config import settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> logging.Logger:
    log_dir = settings.root / "logs"
    log_dir.mkdir(exist_ok=True)
    logger = logging.getLogger("scamtrace")
    if logger.handlers:
        return logger
    logger.setLevel(settings.log_level.upper())
    handler = logging.FileHandler(log_dir / "scamtrace.jsonl", encoding="utf-8")
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = configure_logging()

