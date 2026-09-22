"""Fuse independent signals into an explainable, non-probabilistic threat score."""

from __future__ import annotations

from typing import Any


def risk_level(score: int, has_strong_signal: bool = False) -> str:
    if score >= 72 or (score >= 62 and has_strong_signal):
        return "CRITICAL"
    if score >= 46:
        return "HIGH"
    if score >= 24:
        return "VERIFY"
    return "LOW"


def fuse_evidence(
    classifier: dict[str, Any],
    tactics: list[dict[str, Any]],
    progression: dict[str, Any],
    voice: dict[str, Any],
    narrative: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return transparent score components. This is not a scam probability."""
    tactic_component = min(58.0, sum(item["weight"] * item["confidence"] for item in tactics))
    # The language baseline is deliberately capped. Explicit behavioral
    # tactics and progression must dominate, avoiding generic spoken wording
    # turning into an undue warning.
    language_component = max(0.0, (float(classifier.get("scam_score", 0.5)) - 0.35) * 18.0)
    progression_component = min(24.0, float(progression.get("momentum", 0)) * 0.24)
    voice_component = 0.0
    if voice.get("label") == "synthetic":
        voice_component = min(8.0, float(voice.get("synthetic_score", 0)) * 0.08)
    elif voice.get("label") == "uncertain" and float(voice.get("synthetic_score", 0)) >= 78:
        voice_component = 2.0
    diversity_bonus = min(10.0, max(0, len(tactics) - 2) * 2.5)
    direct_action_tactics = {"FINANCIAL_ACTION", "CREDENTIAL_REQUEST", "REMOTE_ACCESS"}
    direct_action = sorted(item["tactic"] for item in tactics if item["tactic"] in direct_action_tactics)
    # A concrete request that can immediately lose money or control of a device
    # merits a verification warning even when it appears alone. This is an
    # intervention rule, not a probability adjustment.
    # Multiple distinct direct-action demands (for example, credentials plus
    # money) are materially more dangerous than a single ambiguous mention.
    direct_action_component = min(20.0, 10.0 * len(direct_action))
    narrative = narrative or {}
    top_path = narrative.get("top_path") or {}
    # Playbook alignment is a capped reinforcement for a coherent, observed
    # chain. It does not replace a direct request or become a probability.
    narrative_component = min(8.0, max(0.0, float(narrative.get("risk_reinforcement", 0))))
    score = int(round(min(
        100.0,
        tactic_component + language_component + progression_component + voice_component + diversity_bonus + direct_action_component + narrative_component,
    )))
    strong = bool(direct_action)
    level = risk_level(score, strong)
    signals = [
        {
            "name": "Scam language baseline",
            "value": round(float(classifier.get("scam_score", 0.5)) * 100),
            "status": classifier.get("label", "uncertain"),
            "contribution": round(language_component, 1),
        },
        {
            "name": "Behavioral tactics",
            "value": len(tactics),
            "status": "detected" if tactics else "none",
            "contribution": round(tactic_component, 1),
        },
        {
            "name": "Attack progression",
            "value": progression.get("momentum", 0),
            "status": progression.get("current_state", "NORMAL"),
            "contribution": round(progression_component, 1),
        },
        {
            "name": "Voice authenticity",
            "value": voice.get("synthetic_score", 0),
            "status": voice.get("label", "uncertain"),
            "contribution": round(voice_component, 1),
        },
    ]
    if direct_action:
        signals.append({
            "name": "Direct loss or account-control request",
            "value": len(direct_action),
            "status": ", ".join(item.replace("_", " ").lower() for item in direct_action),
            "contribution": round(direct_action_component, 1),
        })
    if top_path:
        signals.append({
            "name": "Attack-path coherence",
            "value": top_path.get("alignment_score", 0),
            "status": f"{top_path.get('name', 'attack path')} · {top_path.get('maturity', 'emerging')}",
            "contribution": round(narrative_component, 1),
        })
    reasons = [
        {
            "title": item["tactic"].replace("_", " ").title(),
            "detail": item["explanation"],
            "evidence": [entry["phrase"] for entry in item["evidence"][:3]],
        }
        for item in tactics
    ]
    if not reasons:
        reasons = [{
            "title": "No high-confidence manipulation pattern",
            "detail": "No direct social-engineering tactic was detected in the supplied conversation.",
            "evidence": [],
        }]
    return {
        "score": score,
        "level": level,
        "signals": signals,
        "reasons": reasons,
        "recommendations": recommendations(level, tactics),
        "components": {
            "language": round(language_component, 1),
            "tactics": round(tactic_component, 1),
            "progression": round(progression_component, 1),
            "voice": round(voice_component, 1),
            "cross_signal": round(diversity_bonus, 1),
            "direct_action": round(direct_action_component, 1),
            "narrative": round(narrative_component, 1),
        },
        "disclaimer": "Threat Score is an evidence-based momentum indicator, not a calibrated probability or legal finding.",
    }


def recommendations(level: str, tactics: list[dict[str, Any]]) -> list[str]:
    names = {item["tactic"] for item in tactics}
    if level in {"HIGH", "CRITICAL"}:
        result = [
            "End the interaction. Do not share OTP, PIN, password, CVV, or identity documents.",
            "Do not transfer money, scan QR codes, share your screen, or install remote-access apps.",
            "Verify independently using an official number or website you find yourself.",
            "Speak with someone you trust before taking any financial action.",
        ]
        if "FINANCIAL_ACTION" in names or "CREDENTIAL_REQUEST" in names:
            result.append("If money or credentials were shared, contact your bank immediately and use India's cybercrime helpline 1930 where appropriate.")
        return result
    if level == "VERIFY":
        return [
            "Pause before acting and independently verify the caller's identity.",
            "Never disclose OTP, PIN, passwords, or banking details on an unsolicited call.",
            "Use an official contact channel rather than a number provided by the caller.",
        ]
    return [
        "No high-risk manipulation pattern is currently detected.",
        "Continue to avoid sharing secrets or making payments on unsolicited calls.",
    ]
