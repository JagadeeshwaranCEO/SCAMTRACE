import json

from backend.attack_engine.narrative import THREAT_NARRATIVE_SCHEMA
from backend.service import ScamTraceService


def test_threat_narrative_has_versioned_graph_with_timestamped_provenance() -> None:
    service = ScamTraceService()
    result = service.analyze_scenario("human_digital_arrest")
    narrative = result["narrative"]
    graph = narrative["graph"]
    assert narrative["schema"] == THREAT_NARRATIVE_SCHEMA
    assert graph["schema"] == THREAT_NARRATIVE_SCHEMA
    evidence_nodes = [node for node in graph["nodes"] if node["type"] == "evidence"]
    assert evidence_nodes
    assert all(node["source"] == "LOCAL_TRANSCRIPT" for node in evidence_nodes)
    assert all("source_timestamp_seconds" in node and "confidence" in node for node in evidence_nodes)
    assert all("raw_text" not in node and "caller" not in node for node in evidence_nodes)
    assert any(edge["type"] == "ALIGNS_WITH" for edge in graph["edges"])


def test_report_redacts_sensitive_values_by_default_but_not_when_explicitly_requested() -> None:
    service = ScamTraceService()
    result = service.analyze_text(
        "This is the bank fraud department. Do not disconnect. Tell me your OTP 123456, "
        "PAN ABCDE1234F and Aadhaar 1234 5678 9012. Send money to fraudster@upi immediately.",
        "en",
    )
    redacted = service.report(result)
    text = json.dumps(redacted, ensure_ascii=False)
    for sensitive in ("123456", "ABCDE1234F", "1234 5678 9012", "fraudster@upi"):
        assert sensitive not in text
    assert redacted["export_privacy"]["mode"] == "REDACTED_BY_DEFAULT"
    assert "OTP" in redacted["export_privacy"]["redaction_categories"]
    assert redacted["user_initiated_escalation"]["automatic_submission"].startswith("NO")
    unredacted = service.report(result, include_sensitive_evidence=True)
    assert "123456" in json.dumps(unredacted, ensure_ascii=False)
    assert unredacted["export_privacy"]["mode"] == "LOCAL_UNREDACTED_BY_EXPLICIT_USER_CHOICE"


def test_feedback_and_drift_are_content_free_and_cannot_change_alerts() -> None:
    service = ScamTraceService()
    result = service.analyze_text("This is a normal appointment reminder for tomorrow.", "en")
    before_level = result["fusion"]["level"]
    observation = result["drift"]
    assert observation["raw_content_retained"] == "NO"
    assert "appointment" not in json.dumps(observation)
    receipt = service.record_feedback(
        result["analysis_id"], "UNSURE", result["transcript"]["language"], before_level, result["fusion"]["score"]
    )
    assert receipt["accepted"] is True
    assert receipt["automatic_retraining"] == "NO"
    after = service.analyze_text("This is a normal appointment reminder for tomorrow.", "en")
    assert after["fusion"]["level"] == before_level
