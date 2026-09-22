"""Default-redaction utilities for local incident export.

The analysis view can show a user their own transcript in active memory. An
export is a different trust boundary: it may later be shared with a bank,
family member, or reporting channel. We therefore remove common credential and
identity values by default before an incident record is written to disk.
"""

from __future__ import annotations

import re
from typing import Any


REDACTION_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("OTP", re.compile(r"\b(?:otp|one[- ]?time password|verification code)\b\s*(?:is|:|=)?\s*\d{4,8}\b", re.IGNORECASE), "[REDACTED_OTP]"),
    ("CVV_OR_PIN", re.compile(r"\b(?:cvv|pin)\b\s*(?:is|:|=)?\s*\d{3,6}\b", re.IGNORECASE), "[REDACTED_CREDENTIAL]"),
    ("AADHAAR", re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b"), "[REDACTED_AADHAAR]"),
    ("PAN", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE), "[REDACTED_PAN]"),
    ("UPI_ID", re.compile(r"\b[a-z0-9._-]{2,}@[a-z][a-z0-9.-]{1,}\b", re.IGNORECASE), "[REDACTED_UPI_ID]"),
    ("CARD_NUMBER", re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[REDACTED_CARD_OR_ACCOUNT]"),
    ("EMAIL", re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.IGNORECASE), "[REDACTED_EMAIL]"),
    ("PHONE", re.compile(r"(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)"), "[REDACTED_PHONE]"),
)


def redact_value(value: Any, categories: set[str] | None = None) -> Any:
    """Deep-copy JSON-compatible values while redacting likely sensitive data."""
    categories = categories if categories is not None else set()
    if isinstance(value, dict):
        return {str(key): redact_value(item, categories) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_value(item, categories) for item in value]
    if not isinstance(value, str):
        return value
    redacted = value
    for category, pattern, replacement in REDACTION_RULES:
        redacted, replacements = pattern.subn(replacement, redacted)
        if replacements:
            categories.add(category)
    return redacted
