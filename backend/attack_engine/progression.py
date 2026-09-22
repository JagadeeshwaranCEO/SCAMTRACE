"""Non-linear attack progression and scam-momentum calculation."""

from __future__ import annotations

from typing import Any


STAGE_ORDER = [
    "NORMAL",
    "IDENTITY_CLAIM",
    "AUTHORITY_IMPERSONATION",
    "FEAR_ESCALATION",
    "URGENCY",
    "ISOLATION",
    "CREDENTIAL_EXTRACTION",
    "FINANCIAL_EXTRACTION",
    "CRITICAL",
]
STAGE_INDEX = {stage: index for index, stage in enumerate(STAGE_ORDER)}
CRITICAL_TACTICS = {"FINANCIAL_ACTION", "REMOTE_ACCESS"}


def _highest_stage(tactics: list[dict[str, Any]], accumulated_tactics: set[str] | None = None) -> str:
    if not tactics:
        return "NORMAL"
    candidate = max((item["stage"] for item in tactics), key=lambda stage: STAGE_INDEX.get(stage, 0))
    names = {item["tactic"] for item in tactics}
    all_names = names | (accumulated_tactics or set())
    if ("FINANCIAL_ACTION" in all_names and ("THREAT" in all_names or "ISOLATION" in all_names)) or (
        "REMOTE_ACCESS" in all_names and "CREDENTIAL_REQUEST" in all_names
    ):
        return "CRITICAL"
    return candidate


def build_progression(
    segments: list[dict[str, Any]],
    findings_by_segment: list[list[dict[str, Any]]],
) -> dict[str, Any]:
    """Accumulate evidence over time. Scores describe momentum, not probability."""
    momentum = 3.0
    seen_tactics: set[str] = set()
    state_history: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    momentum_points: list[dict[str, Any]] = []
    current_state = "NORMAL"

    for segment, findings in zip(segments, findings_by_segment):
        start = float(segment.get("start", 0.0))
        new_tactics = {item["tactic"] for item in findings} - seen_tactics
        repeated_tactics = {item["tactic"] for item in findings} & seen_tactics
        evidence_gain = sum(item["weight"] * item["confidence"] for item in findings if item["tactic"] in new_tactics)
        repeat_gain = sum(item["weight"] * 0.16 for item in findings if item["tactic"] in repeated_tactics)
        cross_signal_bonus = 6 if len(new_tactics) >= 2 else 0
        momentum = max(0.0, min(100.0, momentum * 0.96 + evidence_gain * 0.63 + repeat_gain + cross_signal_bonus))
        proposed_state = _highest_stage(findings, seen_tactics)
        if STAGE_INDEX[proposed_state] > STAGE_INDEX[current_state]:
            current_state = proposed_state
            state_event = {
                "time": start,
                "state": current_state,
                "confidence": round(max((item["confidence"] for item in findings), default=0.4), 2),
                "evidence": [item["tactic"] for item in findings],
                "summary": _state_summary(current_state),
            }
            state_history.append(state_event)
            timeline.append(state_event)
        seen_tactics.update(item["tactic"] for item in findings)
        momentum_points.append({"time": start, "score": round(momentum), "state": current_state})

    timeline.sort(key=lambda item: (item["time"], 0 if "tactic" not in item else 1))
    return {
        "current_state": current_state,
        "state_history": state_history,
        "timeline": timeline,
        "momentum": round(momentum),
        "momentum_points": momentum_points or [{"time": 0.0, "score": 3, "state": "NORMAL"}],
        "seen_tactics": sorted(seen_tactics),
    }


def _state_summary(state: str) -> str:
    summaries = {
        "IDENTITY_CLAIM": "Identity claim detected",
        "AUTHORITY_IMPERSONATION": "Authority impersonation detected",
        "FEAR_ESCALATION": "Fear or legal-threat escalation detected",
        "URGENCY": "Urgency pressure detected",
        "ISOLATION": "Isolation attempt detected",
        "CREDENTIAL_EXTRACTION": "Credential or access extraction detected",
        "FINANCIAL_EXTRACTION": "Financial extraction stage detected",
        "CRITICAL": "Cross-signal critical escalation detected",
        "NORMAL": "No attack stage detected",
    }
    return summaries[state]
