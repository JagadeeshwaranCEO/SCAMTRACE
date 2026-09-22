"""Conservative local normalization for common security-term ASR errors.

This is not a general grammar rewriter. It changes only high-value entities
whose common spacing/spelling variants would otherwise hide an attack tactic.
The original transcript and every applied correction remain available in the
analysis response.
"""

from __future__ import annotations

import re


REPLACEMENTS: tuple[tuple[str, str], ...] = (
    (r"\bo\s*[-.]?\s*t\s*[-.]?\s*p\b", "OTP"),
    (r"\bone[\s-]?time password\b", "OTP"),
    (r"\bc\s*[-.]?\s*v\s*[-.]?\s*v\b", "CVV"),
    (r"\bu\s*[-.]?\s*p\s*[-.]?\s*i\b", "UPI"),
    (r"\bk\s*[-.]?\s*y\s*[-.]?\s*c\b", "KYC"),
    (r"\bc\s*[-.]?\s*b\s*[-.]?\s*i\b", "CBI"),
    (r"\br\s*[-.]?\s*b\s*[-.]?\s*i\b", "RBI"),
    (r"\bcyber[\s-]?crime\b", "cybercrime"),
    (r"\bany[\s-]?desk\b", "AnyDesk"),
    (r"\bteam[\s-]?viewer\b", "TeamViewer"),
    (r"\ba[ae]d+h?a?r\b", "Aadhaar"),
)


def normalize_security_terms(value: str) -> tuple[str, list[dict[str, str]]]:
    """Return a normalized transcript plus an audit trail of substitutions."""
    text = str(value)
    corrections: list[dict[str, str]] = []
    for pattern, replacement in REPLACEMENTS:
        def replace(match: re.Match[str]) -> str:
            original = match.group(0)
            if original != replacement:
                corrections.append({"from": original, "to": replacement})
            return replacement
        text = re.sub(pattern, replace, text, flags=re.IGNORECASE)
    return text, corrections
