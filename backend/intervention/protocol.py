"""Choose a safe, explainable interruption without engaging the alleged caller."""

from __future__ import annotations

from typing import Any


def build_counter_pressure_protocol(
    fusion: dict[str, Any],
    tactics: list[dict[str, Any]],
    narrative: dict[str, Any],
) -> dict[str, Any]:
    """Return bounded, threat-aware actions; never auto-report or contact anyone."""
    level = str(fusion.get("level", "LOW"))
    names = {item["tactic"] for item in tactics}
    top_path = narrative.get("top_path") or {}
    if level == "LOW":
        return {
            "mode": "MONITOR",
            "headline": "No active coercion chain detected",
            "purpose": "Keep normal caution without creating an unnecessary interruption.",
            "steps": [
                _step("Keep secrets private", "Do not share OTPs, PINs, passwords, CVV or identity documents on unsolicited calls.", "baseline"),
                _step("Verify unexpected requests independently", "Use a contact number or website you find yourself, not one supplied during a call.", "verification"),
            ],
            "read_aloud": "I will verify this independently before I share information or take any action.",
            "counterfactual": "No coherent high-risk attack path is currently observed.",
            "automatic_actions": "NONE — SCAMTRACE never contacts a caller, bank, police service or reporting portal for you.",
        }

    steps = [_step("End the interaction", _end_call_message(names, top_path), "stop")]
    if "ISOLATION" in names:
        steps.append(_step("Break the isolation attempt", "Tell a trusted person what happened before making any payment, disclosure or installation decision.", "break_isolation"))
    if "TAMPER_EVASION" in names:
        steps.append(_step("Keep protections active", "Do not disable a safety app, mute warnings, or close the evidence screen because a caller tells you to. End the interaction first and seek independent help.", "resist_tamper"))
    if names & {"CREDENTIAL_REQUEST", "REMOTE_ACCESS"}:
        steps.append(_step("Protect account and device access", _account_access_message(names), "contain_access"))
    if "FINANCIAL_ACTION" in names:
        steps.append(_step("Stop movement of money", "Do not transfer funds, scan a QR code, add a beneficiary or pay a so-called verification, release or safe-account charge.", "contain_funds"))
    steps.append(_step("Verify independently", _verification_message(top_path), "verification"))
    if names & {"FINANCIAL_ACTION", "CREDENTIAL_REQUEST", "REMOTE_ACCESS"}:
        steps.append(_step("Contain any completed action", "If you already shared credentials, installed remote access or transferred money, contact your bank using its official channel immediately. Use India's cybercrime helpline 1930 where appropriate.", "recovery"))

    status = "CRITICAL INTERRUPTION" if level == "CRITICAL" else "PROTECTIVE PAUSE"
    read_aloud = "I am ending this call and will verify through an official contact I find myself. I will not share any code, install an app or transfer money."
    return {
        "mode": status,
        "headline": top_path.get("name", "Potential social-engineering attack"),
        "purpose": "Interrupt pressure before an irreversible action. This is decision support, not a criminal accusation.",
        "steps": steps,
        "read_aloud": read_aloud,
        "counterfactual": top_path.get("counterfactual", "Concern would reduce only after the request is independently verified through an official channel you find yourself."),
        "automatic_actions": "NONE — SCAMTRACE never contacts a caller, bank, police service or reporting portal for you.",
        "playbook": {
            "id": top_path.get("id"),
            "name": top_path.get("name"),
            "maturity": top_path.get("maturity"),
            "alignment_score": top_path.get("alignment_score"),
            "alignment_label": top_path.get("alignment_label"),
        } if top_path else None,
    }


def _step(title: str, action: str, category: str) -> dict[str, str]:
    return {"title": title, "action": action, "category": category}


def _end_call_message(names: set[str], top_path: dict[str, Any]) -> str:
    if top_path.get("safe_exit"):
        return str(top_path["safe_exit"])
    if "ISOLATION" in names:
        return "End the interaction. A legitimate organisation can be verified after you disconnect; do not remain on a secret call."
    return "Pause the interaction before you share information or take action."


def _account_access_message(names: set[str]) -> str:
    if "REMOTE_ACCESS" in names:
        return "Do not install AnyDesk, TeamViewer or another remote-control app. Do not share your screen. If software was installed, disconnect it and seek help from a trusted device."
    return "Do not reveal OTPs, PINs, CVV, passwords, verification codes or identity-document details."


def _verification_message(top_path: dict[str, Any]) -> str:
    path_id = top_path.get("id")
    if path_id == "family_emergency_payment":
        return "Call the family member or hospital using a saved contact or independently found official number—not the caller's number."
    if path_id == "courier_customs_extortion":
        return "Check the parcel only through the courier's official website or independently found customer-care number."
    if path_id == "bank_account_takeover":
        return "Open your bank's official app or use the contact number printed on your card. Do not use a number sent or spoken by the caller."
    return "Find the organisation's official website or published contact number yourself. Verify there, after the call is ended."
