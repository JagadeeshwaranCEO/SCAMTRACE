"""Bounded attack-path inference with inspectable evidence provenance.

The narrative graph does not identify callers or estimate scam probability. It
compares timestamped, detected social-engineering behaviours with a small set of
auditable attack playbooks, so the intervention layer can explain *why now*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.utils.text import normalize_text


THREAT_NARRATIVE_SCHEMA = "scamtrace.threat-narrative-graph/1.0"
TAXONOMY_VERSION = "scamtrace-tactic-taxonomy/1.1"


@dataclass(frozen=True)
class Playbook:
    identifier: str
    name: str
    description: str
    anchors: tuple[str, ...]
    requirements: tuple[frozenset[str], ...]
    counterfactual: str
    safe_exit: str


PLAYBOOKS: tuple[Playbook, ...] = (
    Playbook(
        "digital_arrest",
        "Digital-arrest coercion",
        "An authority claim is used with criminal allegations, secrecy and a money or credential demand.",
        ("cybercrime", "cyber crime", "police", "cbi", "rbi", "enforcement directorate", "ed officer", "arrest", "money laundering", "साइबर क्राइम", "पुलिस", "गिरफ्तार", "சைபர் கிரைம்", "காவல் துறை", "வழக்கு பதிவு"),
        (
            frozenset({"AUTHORITY_IMPERSONATION", "IDENTITY_CLAIM"}),
            frozenset({"THREAT"}),
            frozenset({"ISOLATION"}),
            frozenset({"FINANCIAL_ACTION", "CREDENTIAL_REQUEST"}),
        ),
        "Concern would reduce only after the alleged agency is independently reached through an official contact you find yourself and confirms the claim.",
        "End the call. Do not stay isolated or transfer money to a so-called safe account.",
    ),
    Playbook(
        "bank_account_takeover",
        "Bank-account takeover",
        "A bank or KYC identity is used to obtain authentication factors, screen access or a payment.",
        ("bank", "kyc", "otp", "cvv", "account", "aadhaar", "pan"),
        (
            frozenset({"AUTHORITY_IMPERSONATION", "IDENTITY_CLAIM", "TRUST_BUILDING"}),
            frozenset({"THREAT", "URGENCY"}),
            frozenset({"CREDENTIAL_REQUEST", "REMOTE_ACCESS"}),
            frozenset({"FINANCIAL_ACTION", "ISOLATION"}),
        ),
        "Concern would reduce only after you independently contact the bank using a number from its official app, card or website—not a number supplied in the call.",
        "Do not reveal an OTP, PIN, CVV or password. Do not install an app or share your screen.",
    ),
    Playbook(
        "courier_customs_extortion",
        "Courier or customs extortion",
        "A parcel or customs story is used to create legal fear and force an immediate payment or remote action.",
        ("courier", "customs", "parcel", "shipment", "prohibited documents"),
        (
            frozenset({"AUTHORITY_IMPERSONATION", "IDENTITY_CLAIM"}),
            frozenset({"THREAT", "URGENCY"}),
            frozenset({"ISOLATION", "REMOTE_ACCESS"}),
            frozenset({"FINANCIAL_ACTION", "CREDENTIAL_REQUEST"}),
        ),
        "Concern would reduce only after you independently verify the shipment through the courier's official tracking channel or customer-care contact.",
        "End the interaction and verify any parcel from the official courier site. Do not pay a release or processing charge during the call.",
    ),
    Playbook(
        "family_emergency_payment",
        "Family-emergency payment coercion",
        "An emergency narrative is used to bypass normal family verification and force payment.",
        ("family emergency", "accident", "hospital", "your son", "your daughter", "family"),
        (
            frozenset({"FAMILY_EMERGENCY"}),
            frozenset({"THREAT", "URGENCY"}),
            frozenset({"ISOLATION"}),
            frozenset({"FINANCIAL_ACTION", "CREDENTIAL_REQUEST"}),
        ),
        "Concern would reduce only after you contact the family member or hospital using a saved or independently discovered number.",
        "Pause. Call your family member or hospital through a trusted number before sending any money.",
    ),
    Playbook(
        "remote_device_takeover",
        "Remote-device takeover",
        "A caller attempts to gain device or screen access and then collect account credentials or funds.",
        ("anydesk", "teamviewer", "remote access", "share your screen", "screen sharing", "install this app"),
        (
            frozenset({"AUTHORITY_IMPERSONATION", "TRUST_BUILDING"}),
            frozenset({"URGENCY", "THREAT", "ISOLATION"}),
            frozenset({"REMOTE_ACCESS"}),
            frozenset({"CREDENTIAL_REQUEST", "FINANCIAL_ACTION"}),
        ),
        "Concern would reduce only after an independently contacted organisation confirms that no remote-support session is needed.",
        "Do not install remote-access software or share your screen. If an app was installed, disconnect it and contact your bank from a trusted device.",
    ),
)


def build_attack_narrative(
    segments: list[dict[str, Any]],
    findings_by_segment: list[list[dict[str, Any]]],
) -> dict[str, Any]:
    """Build compact event provenance and ranked bounded playbook alignment."""
    events = _events(segments, findings_by_segment)
    observed_tactics = {event["tactic"] for event in events}
    text = normalize_text(" ".join(str(segment.get("text", "")) for segment in segments))
    paths = [_evaluate_playbook(playbook, text, observed_tactics, events) for playbook in PLAYBOOKS]
    paths = [path for path in paths if path is not None]
    paths.sort(key=lambda path: (path["alignment_score"], path["maturity_rank"], path["id"]), reverse=True)
    top = paths[0] if paths else None
    reinforcement = 0
    if top:
        reinforcement = {"emerging": 0, "active": 4, "critical": 8}[top["maturity"]]
    graph = _build_graph(events, paths)
    return {
        "schema": THREAT_NARRATIVE_SCHEMA,
        "method": "SCAMTRACE Threat Narrative Graph v1 — deterministic bounded playbook alignment",
        "taxonomy_version": TAXONOMY_VERSION,
        "events": events,
        "graph": graph,
        "paths": paths[:3],
        "top_path": top,
        "risk_reinforcement": reinforcement,
        "disclaimer": "Playbook alignment describes observed conversational behaviour. It is not a caller-identity claim, criminal finding or probability.",
    }


def _events(segments: list[dict[str, Any]], findings_by_segment: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for segment_index, (segment, findings) in enumerate(zip(segments, findings_by_segment)):
        timestamp = round(float(segment.get("start", 0.0)), 2)
        for finding in findings:
            evidence = finding.get("evidence") or [{}]
            for item in evidence[:2]:
                values.append({
                    "event_id": f"e{segment_index + 1}_{finding['tactic'].lower()}_{len(values) + 1}",
                    "segment_index": segment_index,
                    "time": timestamp,
                    "source_timestamp_seconds": timestamp,
                    "source": "LOCAL_TRANSCRIPT",
                    "detection_method": TAXONOMY_VERSION,
                    "tactic": finding["tactic"],
                    "stage": finding["stage"],
                    "confidence": float(finding.get("confidence", 0.0)),
                    "phrase": item.get("phrase", "detected tactic"),
                    "summary": finding["explanation"],
                })
    return sorted(values, key=lambda item: (item["time"], item["segment_index"], item["tactic"]))


def _evaluate_playbook(
    playbook: Playbook,
    text: str,
    observed_tactics: set[str],
    events: list[dict[str, Any]],
) -> dict[str, Any] | None:
    anchor_hit = any(anchor in text for anchor in playbook.anchors)
    if not anchor_hit:
        return None
    matched_steps: list[dict[str, Any]] = []
    for index, alternatives in enumerate(playbook.requirements):
        candidates = [event for event in events if event["tactic"] in alternatives]
        if candidates:
            event = min(candidates, key=lambda value: (value["time"], value["segment_index"]))
            matched_steps.append({
                "order": index + 1,
                "tactics": sorted(alternatives),
                "event_id": event["event_id"],
                "time": event["time"],
                "tactic": event["tactic"],
                "phrase": event["phrase"],
            })
    if len(matched_steps) < 2:
        return None
    coverage = len(matched_steps) / len(playbook.requirements)
    order_pairs = list(zip(matched_steps, matched_steps[1:]))
    ordered_pairs = sum(right["time"] >= left["time"] for left, right in order_pairs)
    order_coherence = ordered_pairs / len(order_pairs) if order_pairs else 0.5
    direct_action = bool(observed_tactics & {"FINANCIAL_ACTION", "CREDENTIAL_REQUEST", "REMOTE_ACCESS"})
    alignment = round(min(100, 100 * (coverage * 0.7 + order_coherence * 0.18 + (0.12 if direct_action else 0))))
    maturity = _maturity(coverage, direct_action, observed_tactics)
    expected_next = _expected_next(playbook, observed_tactics)
    return {
        "id": playbook.identifier,
        "name": playbook.name,
        "summary": playbook.description,
        "alignment_score": alignment,
        "alignment_label": "behavioural alignment — not probability",
        "maturity": maturity,
        "maturity_rank": {"emerging": 1, "active": 2, "critical": 3}[maturity],
        "matched_steps": matched_steps,
        "missing_steps": expected_next,
        "counterfactual": playbook.counterfactual,
        "safe_exit": playbook.safe_exit,
        "direct_action_observed": direct_action,
    }


def _build_graph(events: list[dict[str, Any]], paths: list[dict[str, Any]]) -> dict[str, Any]:
    """Emit a stable graph envelope that can be ingested or audited locally.

    The graph intentionally contains tactic evidence and time references, but
    no full transcript, caller identity, device identifier, or criminal claim.
    """
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    observed_tactics = sorted({event["tactic"] for event in events})
    for tactic in observed_tactics:
        nodes.append({
            "id": f"tactic:{tactic}",
            "type": "tactic",
            "label": tactic,
            "taxonomy_version": TAXONOMY_VERSION,
        })
    for event in events:
        nodes.append({
            "id": event["event_id"],
            "type": "evidence",
            "source": event["source"],
            "source_timestamp_seconds": event["source_timestamp_seconds"],
            "segment_index": event["segment_index"],
            "tactic": event["tactic"],
            "stage": event["stage"],
            "confidence": event["confidence"],
            "detection_method": event["detection_method"],
            "evidence_phrase": event["phrase"],
        })
        edges.append({
            "id": f"{event['event_id']}->tactic:{event['tactic']}",
            "type": "SUPPORTS",
            "from": event["event_id"],
            "to": f"tactic:{event['tactic']}",
            "confidence": event["confidence"],
            "source_timestamp_seconds": event["source_timestamp_seconds"],
        })
    for path in paths[:3]:
        playbook_id = f"playbook:{path['id']}"
        nodes.append({
            "id": playbook_id,
            "type": "playbook",
            "label": path["name"],
            "maturity": path["maturity"],
            "alignment_score": path["alignment_score"],
            "alignment_label": path["alignment_label"],
        })
        by_tactic: dict[str, list[dict[str, Any]]] = {}
        for step in path["matched_steps"]:
            by_tactic.setdefault(step["tactic"], []).append(step)
        for tactic, steps in by_tactic.items():
            evidence_ids = [step["event_id"] for step in steps]
            edges.append({
                "id": f"tactic:{tactic}->{playbook_id}",
                "type": "ALIGNS_WITH",
                "from": f"tactic:{tactic}",
                "to": playbook_id,
                "confidence": round(path["alignment_score"] / 100, 4),
                "source_timestamp_seconds": min(step["time"] for step in steps),
                "evidence_ids": evidence_ids,
            })
    return {
        "schema": THREAT_NARRATIVE_SCHEMA,
        "scope": "Local bounded behavioural evidence. No caller identity, raw transcript, or criminal conclusion.",
        "nodes": nodes,
        "edges": edges,
    }


def _maturity(coverage: float, direct_action: bool, observed_tactics: set[str]) -> str:
    if direct_action and coverage >= 0.75 and ("THREAT" in observed_tactics or "ISOLATION" in observed_tactics):
        return "critical"
    if coverage >= 0.5 or (direct_action and coverage >= 0.25):
        return "active"
    return "emerging"


def _expected_next(playbook: Playbook, observed_tactics: set[str]) -> list[str]:
    for alternatives in playbook.requirements:
        if not (alternatives & observed_tactics):
            return sorted(alternatives)
    return []
