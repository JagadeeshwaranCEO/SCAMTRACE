"""Create a privacy-aware JSON incident report without persisting audio."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from backend.reports.redaction import redact_value


def incident_report(result: dict[str, Any], include_sensitive_evidence: bool = False) -> dict[str, Any]:
    """Create a local report, redacting sensitive values unless opted in."""
    categories: set[str] = set()
    transcript = {
        "text": result["transcript"].get("text", ""),
        "language": result["transcript"].get("language", "auto"),
        "segments": result["transcript"].get("segments", []),
        "engine": result["transcript"].get("engine", "unknown"),
    }
    payload = {
        "report_type": "SCAMTRACE INCIDENT REPORT",
        "generated_at": datetime.now(UTC).isoformat(),
        "disclaimer": "Potential social-engineering indicators detected. This report is decision support, not a legal accusation.",
        "threat_level": result["fusion"]["level"],
        "threat_score": result["fusion"]["score"],
        "detected_attack_categories": result["attack_categories"],
        "detected_tactics": [
            {"tactic": item["tactic"], "confidence": item["confidence"], "evidence": item["evidence"]}
            for item in result["tactics"]
        ],
        "attack_timeline": result["progression"]["timeline"],
        "scam_momentum": result["progression"]["momentum_points"],
        "threat_narrative": result.get("narrative", {}),
        "counter_pressure_protocol": result.get("intervention", {}),
        "voice_authenticity": result["voice"],
        "transcript": transcript,
        "recommended_actions": result["fusion"]["recommendations"],
        "privacy_processing_mode": result["privacy"],
        "model_coverage_observation": result.get("drift", {}),
        "user_initiated_escalation": _escalation_handoff(result),
        "model_versions": {
            "language": result["classifier"].get("model_version", "unavailable"),
            "voice": result["voice"].get("model", "unavailable"),
            "asr": result["transcript"].get("engine", "text input"),
        },
    }
    if include_sensitive_evidence:
        payload["export_privacy"] = {
            "mode": "LOCAL_UNREDACTED_BY_EXPLICIT_USER_CHOICE",
            "warning": "This file may contain credentials or identity values. Share it only through a channel you trust.",
            "raw_text_field_included": "NO — original ASR text is never exported separately.",
        }
        return payload
    redacted = redact_value(payload, categories)
    redacted["export_privacy"] = {
        "mode": "REDACTED_BY_DEFAULT",
        "redaction_categories": sorted(categories),
        "raw_text_field_included": "NO",
        "note": "Likely credential and identity values were removed before this local file was created.",
    }
    return redacted


def _escalation_handoff(result: dict[str, Any]) -> dict[str, Any]:
    """Prepare a user-controlled handoff without submitting external data."""
    tactics = {item.get("tactic") for item in result.get("tactics", [])}
    loss_or_access_risk = bool(tactics & {"FINANCIAL_ACTION", "CREDENTIAL_REQUEST", "REMOTE_ACCESS"})
    return {
        "automatic_submission": "NO — SCAMTRACE does not contact a bank, 1930, or cybercrime.gov.in.",
        "recommended_when": (
            "If money was sent, credentials were shared, or remote access was granted, act immediately through official channels."
            if loss_or_access_risk else
            "Use only if you decide an official report is appropriate; verify the caller independently first."
        ),
        "official_channels": {
            "india_cybercrime_helpline": "1930",
            "national_cybercrime_reporting_portal": "https://cybercrime.gov.in",
        },
        "prepare_before_you_report": [
            "Your own contact details and the approximate incident time.",
            "Transaction or UPI reference details only if a transaction occurred.",
            "This locally generated report after you review its redaction setting.",
        ],
        "operator_boundary": "SCAMTRACE provides a local, reviewable case summary. The user chooses whether, when, and what to submit.",
    }
