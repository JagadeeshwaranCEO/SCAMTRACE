from backend.attack_engine.progression import build_progression
from backend.classifiers.taxonomy import detect_tactics


def test_progression_accumulates_and_reaches_critical() -> None:
    segments = [
        {"start": 0, "end": 5, "text": "I am calling from the cybercrime department."},
        {"start": 5, "end": 10, "text": "Your account will be blocked due to a criminal case."},
        {"start": 10, "end": 15, "text": "Do not disconnect and do not tell anyone."},
        {"start": 15, "end": 20, "text": "Transfer money to the safe account immediately."},
    ]
    progression = build_progression(segments, [detect_tactics(segment["text"]) for segment in segments])
    assert progression["current_state"] == "CRITICAL"
    assert progression["momentum_points"][-1]["score"] > progression["momentum_points"][0]["score"]
    assert any(event["state"] == "AUTHORITY_IMPERSONATION" for event in progression["state_history"])
    assert any(event["state"] == "CRITICAL" for event in progression["state_history"])


def test_progression_stays_normal_without_evidence() -> None:
    segments = [{"start": 0, "end": 5, "text": "The meeting starts at ten tomorrow."}]
    progression = build_progression(segments, [detect_tactics(segments[0]["text"])])
    assert progression["current_state"] == "NORMAL"
    assert progression["momentum"] <= 3

