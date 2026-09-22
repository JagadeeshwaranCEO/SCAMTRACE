from backend.decision_model.stdm import LABELS, decision_features, predict_stdm, train_stdm
from backend.service import ScamTraceService


def _row(state: str, text: str, tactic: str) -> dict:
    return {
        "state": state,
        "text": text,
        "language": "en",
        "tactics": [{"tactic": tactic, "occurrences": 1}],
        "progression": {"momentum": 20, "current_state": state},
        "classifier": {"label": "scam_language", "scam_score": 0.8},
    }


def test_stdm_trains_a_bounded_distribution(tmp_path) -> None:
    rows = []
    tactics = {
        "NORMAL": "NONE",
        "SUSPICIOUS": "TRUST_BUILDING",
        "IMPERSONATION": "AUTHORITY_IMPERSONATION",
        "MANIPULATION": "THREAT",
        "CREDENTIAL_EXTRACTION": "CREDENTIAL_REQUEST",
        "FINANCIAL_EXTRACTION": "FINANCIAL_ACTION",
    }
    for state in LABELS:
        rows.extend([_row(state, f"{state} evidence alpha", tactics[state]), _row(state, f"{state} evidence beta", tactics[state])])
    model = train_stdm(rows, tmp_path / "stdm.json")
    features = decision_features(
        "Transfer money now", "en", [{"tactic": "FINANCIAL_ACTION", "occurrences": 1}],
        {"momentum": 70, "current_state": "FINANCIAL_EXTRACTION"},
        {"label": "scam_language", "scam_score": 0.9},
    )
    result = predict_stdm(model, features)
    assert set(result["risk_distribution"]) == set(LABELS)
    assert round(sum(result["risk_distribution"].values()), 4) == 1.0


def test_stdm_features_preserve_protective_context() -> None:
    features = decision_features(
        "Never share your OTP. Use the official bank app.", "en", [],
        {"momentum": 0, "current_state": "NORMAL"},
        {"label": "benign_language", "scam_score": 0.1},
    )
    assert "intent:protective_guidance" in features
    assert "intent:protective_secret_advice" in features


def test_service_exposes_stdm_as_shadow_only() -> None:
    service = ScamTraceService()
    result = service.analyze_scenario("human_digital_arrest")
    assert result["decision_model"]["deployment_mode"] == "SHADOW_ONLY"
    assert result["fusion"]["level"] == "CRITICAL"
