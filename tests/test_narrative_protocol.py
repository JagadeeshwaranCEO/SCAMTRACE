from backend.attack_engine.narrative import build_attack_narrative
from backend.classifiers.taxonomy import detect_tactics
from backend.intervention.protocol import build_counter_pressure_protocol
from backend.service import ScamTraceService


def _narrative(segments: list[dict]) -> dict:
    return build_attack_narrative(segments, [detect_tactics(segment["text"]) for segment in segments])


def test_digital_arrest_chain_has_provenance_and_counterfactual() -> None:
    segments = [
        {"start": 0, "end": 5, "text": "I am Officer Rao from the cybercrime department."},
        {"start": 5, "end": 10, "text": "A criminal case means you will be arrested."},
        {"start": 10, "end": 15, "text": "Do not disconnect or tell anyone."},
        {"start": 15, "end": 20, "text": "Transfer money to the safe account immediately."},
    ]
    narrative = _narrative(segments)
    top = narrative["top_path"]
    assert top is not None
    assert top["id"] == "digital_arrest"
    assert top["maturity"] == "critical"
    assert top["alignment_score"] >= 90
    assert len(narrative["events"]) >= 4
    assert narrative["graph"]["nodes"]
    assert narrative["graph"]["edges"]
    assert "independently" in top["counterfactual"].lower()


def test_safety_advice_is_not_misread_as_a_credential_request() -> None:
    text = "Never share OTP, PIN or CVV with a caller. Use your bank's official app to verify any message."
    assert "CREDENTIAL_REQUEST" not in {item["tactic"] for item in detect_tactics(text)}
    narrative = _narrative([{"start": 0, "end": 5, "text": text}])
    assert narrative["top_path"] is None


def test_tamper_prompt_is_visible_but_safety_advice_is_not() -> None:
    assert "TAMPER_EVASION" in {item["tactic"] for item in detect_tactics("That safety app is malware, disable this app now.")}
    assert "TAMPER_EVASION" not in {item["tactic"] for item in detect_tactics("Do not disable this app when an unknown caller asks.")}


def test_protocol_breaks_isolation_without_contacting_the_caller() -> None:
    service = ScamTraceService()
    output = service.analyze_scenario("human_digital_arrest")
    protocol = output["intervention"]
    assert protocol["mode"] == "CRITICAL INTERRUPTION"
    assert protocol["playbook"]["id"] == "digital_arrest"
    assert "official" in protocol["counterfactual"].lower()
    assert protocol["automatic_actions"].startswith("NONE")
    assert any(step["category"] == "break_isolation" for step in protocol["steps"])


def test_safe_synthetic_scenario_stays_in_monitor_mode() -> None:
    service = ScamTraceService()
    output = service.analyze_scenario("ai_voice_safe")
    assert output["fusion"]["level"] == "LOW"
    assert output["narrative"]["top_path"] is None
    assert output["intervention"]["mode"] == "MONITOR"
