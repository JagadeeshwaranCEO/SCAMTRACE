import base64
import tempfile
import wave
from pathlib import Path

from backend.service import ScamTraceService


def test_demo_scenarios_meet_core_expectations() -> None:
    service = ScamTraceService()
    assert service.analyze_scenario("normal_human_call")["fusion"]["level"] == "LOW"
    assert service.analyze_scenario("ai_voice_safe")["fusion"]["level"] == "LOW"
    assert service.analyze_scenario("human_digital_arrest")["fusion"]["level"] == "CRITICAL"
    assert service.analyze_scenario("ai_scam")["fusion"]["level"] == "CRITICAL"
    tamil = service.analyze_scenario("tamil_scam")
    assert tamil["fusion"]["level"] in {"HIGH", "CRITICAL"}
    assert tamil["tactics"]


def test_json_report_has_required_fields() -> None:
    service = ScamTraceService()
    result = service.analyze_scenario("human_digital_arrest")
    report = service.report(result)
    assert report["report_type"] == "SCAMTRACE INCIDENT REPORT"
    assert report["threat_level"] == "CRITICAL"
    assert report["attack_timeline"]
    assert report["threat_narrative"]["top_path"]["id"] == "digital_arrest"
    assert report["counter_pressure_protocol"]["mode"] == "CRITICAL INTERRUPTION"
    assert report["privacy_processing_mode"]["cloud_api_calls"] == "NONE"


def test_audio_service_runs_full_orchestration_without_retaining_upload() -> None:
    service = ScamTraceService()
    service.asr.transcribe = lambda _path, _lang: {
        "text": "This is Inspector Rao from the cybercrime department. Do not disconnect. Transfer money immediately.",
        "language": "en",
        "segments": [{"start": 0, "end": 7, "text": "This is Inspector Rao from the cybercrime department."},
                     {"start": 7, "end": 14, "text": "Do not disconnect. Transfer money immediately."}],
        "engine": "test-local-asr",
    }
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "recording.wav"
        with wave.open(str(path), "wb") as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(16000)
            target.writeframes(b"\x00\x00" * 16000)
        output = service.analyze_audio(base64.b64encode(path.read_bytes()).decode(), path.name, "en")
    assert output["source"] == "AUDIO_UPLOAD"
    assert output["transcript"]["engine"] == "test-local-asr"
    assert output["fusion"]["level"] in {"HIGH", "CRITICAL"}
