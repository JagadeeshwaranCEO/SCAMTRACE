import pytest

from backend.service import ScamTraceService


def test_incremental_session_escalates_without_persistence() -> None:
    service = ScamTraceService()
    session = service.realtime.start("en")
    first = service.realtime.ingest(
        session["session_id"], "I am Officer Rao from the cybercrime department.", 0, 4
    )
    final = service.realtime.ingest(
        session["session_id"], "Do not disconnect. Transfer money to the safe account immediately.", 4, 9
    )
    assert first["realtime"]["persistence"] == "OFF"
    assert final["realtime"]["sequence"] == 2
    assert final["fusion"]["score"] >= first["fusion"]["score"]
    assert final["fusion"]["level"] in {"HIGH", "CRITICAL"}
    closed = service.realtime.close(session["session_id"])
    assert closed["closed"] is True
    with pytest.raises(ValueError):
        service.realtime.snapshot(session["session_id"])


def test_realtime_rejects_invalid_or_empty_segment() -> None:
    service = ScamTraceService()
    session = service.realtime.start()
    with pytest.raises(ValueError):
        service.realtime.ingest(session["session_id"], "")
    with pytest.raises(ValueError):
        service.realtime.snapshot("not-a-session")
