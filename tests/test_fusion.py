from backend.attack_engine.progression import build_progression
from backend.classifiers.taxonomy import detect_tactics
from backend.fusion.evidence import fuse_evidence, risk_level


def make_progression(text: str) -> tuple[list[dict], dict]:
    segments = [{"start": 0, "end": 6, "text": text}]
    tactics = detect_tactics(text)
    return tactics, build_progression(segments, [tactics])


def test_synthetic_safe_voice_is_not_automatically_a_scam() -> None:
    tactics, progression = make_progression("The clinic reminder is scheduled for Tuesday at ten.")
    fusion = fuse_evidence(
        {"scam_score": 0.2, "label": "benign_language"},
        tactics, progression,
        {"label": "synthetic", "synthetic_score": 95, "confidence": 0.9},
    )
    assert fusion["level"] == "LOW"
    assert fusion["score"] < 24
    assert fusion["components"]["voice"] > 0


def test_human_scam_script_is_critical_without_voice_signal() -> None:
    text = (
        "This is Inspector Rao from the cybercrime department. Your account will be blocked "
        "because of a criminal case. Do not disconnect. Transfer money to the safe account immediately."
    )
    tactics, progression = make_progression(text)
    fusion = fuse_evidence(
        {"scam_score": 0.8, "label": "scam_language"},
        tactics, progression,
        {"label": "human", "synthetic_score": 4, "confidence": 0.9},
    )
    assert fusion["level"] == "CRITICAL"
    assert fusion["components"]["voice"] == 0


def test_risk_level_boundaries() -> None:
    assert risk_level(0) == "LOW"
    assert risk_level(24) == "VERIFY"
    assert risk_level(46) == "HIGH"
    assert risk_level(72) == "CRITICAL"

