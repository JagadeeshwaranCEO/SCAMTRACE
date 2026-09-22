"""SCAMTRACE orchestration service: transcript/audio to explainable decision support."""

from __future__ import annotations

import base64
import binascii
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from backend.asr.local_whisper import LocalWhisperEngine
from backend.attack_engine.progression import build_progression
from backend.attack_engine.narrative import build_attack_narrative
from backend.classifiers.scam_classifier import ScamLanguageClassifier
from backend.classifiers.taxonomy import aggregate_tactics, attack_categories, detect_tactics
from backend.config import settings
from backend.decision_model.stdm import StdmDecisionModel
from backend.fusion.evidence import fuse_evidence
from backend.intervention.protocol import build_counter_pressure_protocol
from backend.observability.drift import LocalDriftMonitor
from backend.observability.feedback import LocalFeedbackRegistry
from backend.reports.incident import incident_report
from backend.realtime.session import RealtimeSessionManager
from backend.utils.logging import logger
from backend.utils.text import detect_language, text_segments
from backend.utils.transcript import normalize_security_terms
from backend.voice_auth.acoustic import AcousticAnomalyAuthenticator


ALLOWED_AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".webm", ".flac"}


class ScamTraceService:
    def __init__(self) -> None:
        self.classifier = ScamLanguageClassifier()
        self.decision = StdmDecisionModel()
        self.asr = LocalWhisperEngine()
        self.voice = AcousticAnomalyAuthenticator()
        self.drift = LocalDriftMonitor()
        self.feedback = LocalFeedbackRegistry()
        self.scenarios = self._load_scenarios()
        self.realtime = RealtimeSessionManager(
            self.analyze_text,
            max_sessions=settings.realtime_max_sessions,
            ttl_seconds=settings.realtime_session_ttl_seconds,
            max_segments=settings.realtime_max_segments,
        )

    def status(self) -> dict[str, Any]:
        return {
            "application": "SCAMTRACE",
            "version": "0.4.0",
            "classifier": {
                "available": self.classifier.available,
                "warning": self.classifier.load_error,
                "artifact": str(self.classifier.model_path),
                "model": self.classifier.model.get("model_name") if self.classifier.model else None,
                "version": self.classifier.model.get("version") if self.classifier.model else None,
                "format": self.classifier.model.get("format") if self.classifier.model else None,
            },
            "decision_model": self.decision.status(),
            "asr": self.asr.status(),
            "voice_auth": {
                "available": settings.enable_voice_auth,
                "model": self.voice.model_name,
                "mode": "acoustic anomaly fallback",
                "warning": "A benchmarked anti-spoofing checkpoint is an optional future adapter; fallback never claims a deepfake verdict.",
            },
            "narrative_protocol": {
                "available": settings.enable_narrative_protocol,
                "mode": "versioned bounded attack-path alignment and counter-pressure intervention",
                "persistence": "OFF",
            },
            "drift_monitor": self.drift.status() if settings.enable_drift_monitor else {
                "available": False, "reason": "Disabled by local configuration.",
            },
            "feedback": self.feedback.status() if settings.enable_feedback else {
                "available": False, "reason": "Disabled by local configuration.",
            },
            "privacy": self._privacy(),
            "realtime": {
                "available": True,
                "mode": "local, ephemeral, incremental transcript analysis",
                "transport": "REST segment ingestion",
                "persistence": "OFF",
            },
            "demo_scenarios": [{"id": item["id"], "name": item["name"], "language": item["language"]} for item in self.scenarios],
        }

    def analyze_text(
        self,
        text: str,
        language: str = "auto",
        segments: list[dict[str, Any]] | None = None,
        source: str = "TEXT_INPUT",
        voice: dict[str, Any] | None = None,
        scenario_id: str | None = None,
    ) -> dict[str, Any]:
        original_text = str(text).strip()
        clean_text, transcript_corrections = normalize_security_terms(original_text)
        if not clean_text:
            raise ValueError("Enter a transcript or select a demo scenario.")
        if len(clean_text) > 50_000:
            raise ValueError("Transcript exceeds the 50,000 character safety limit.")
        actual_language = detect_language(clean_text, language)
        segment_items = self._validate_segments(segments) if segments else text_segments(clean_text)
        findings_by_segment = [detect_tactics(item["text"]) for item in segment_items]
        tactics = aggregate_tactics(findings_by_segment)
        progression = build_progression(segment_items, findings_by_segment)
        narrative = build_attack_narrative(segment_items, findings_by_segment) if settings.enable_narrative_protocol else {}
        classifier = self.classifier.predict(clean_text)
        drift = self.drift.observe(classifier, actual_language, tactics) if settings.enable_drift_monitor else {
            "mode": "DISABLED", "persistence": "OFF", "raw_content_retained": "NO",
        }
        voice_result = voice or {
            "synthetic_score": 0.0,
            "label": "uncertain",
            "confidence": 0.0,
            "model": "No audio supplied",
            "available": False,
            "warning": "Voice authenticity is unavailable for text-only analysis.",
        }
        fusion = fuse_evidence(classifier, tactics, progression, voice_result, narrative)
        intervention = build_counter_pressure_protocol(fusion, tactics, narrative)
        decision = self.decision.predict(clean_text, actual_language, tactics, progression, classifier)
        result = {
            "analysis_id": os.urandom(8).hex(),
            "source": source,
            "scenario_id": scenario_id,
            "transcript": {
                "text": clean_text,
                "raw_text": original_text,
                "corrections": transcript_corrections,
                "language": actual_language,
                "segments": segment_items,
                "engine": "scenario transcript" if source == "DEMO_SCENARIO" else "direct text",
            },
            "classifier": classifier,
            "drift": drift,
            "tactics": tactics,
            "attack_categories": attack_categories(tactics),
            "progression": progression,
            "narrative": narrative,
            "voice": voice_result,
            "fusion": fusion,
            "intervention": intervention,
            "decision_model": decision,
            "privacy": self._privacy(),
        }
        logger.info(json.dumps({
            "event": "analysis_complete",
            "analysis_id": result["analysis_id"],
            "source": source,
            "risk_level": fusion["level"],
            "score": fusion["score"],
            "tactic_count": len(tactics),
        }))
        return result

    def analyze_scenario(self, scenario_id: str) -> dict[str, Any]:
        scenario = next((item for item in self.scenarios if item["id"] == scenario_id), None)
        if not scenario:
            raise ValueError("Unknown demo scenario.")
        voice_fixture = scenario.get("voice_fixture")
        # Fixture provenance is explicitly marked. It never affects live/custom
        # audio and is presented as declared demo context, not model inference.
        if voice_fixture:
            voice_fixture = {**voice_fixture, "demo_fixture": True}
        return self.analyze_text(
            scenario["transcript"], scenario.get("language", "auto"), scenario.get("segments"),
            source="DEMO_SCENARIO", voice=voice_fixture, scenario_id=scenario_id,
        )

    def analyze_audio(self, encoded_audio: str, filename: str, language: str = "auto") -> dict[str, Any]:
        if not isinstance(encoded_audio, str) or not encoded_audio:
            raise ValueError("No audio content received.")
        safe_name = Path(filename or "recording.wav").name
        suffix = Path(safe_name).suffix.lower()
        if suffix not in ALLOWED_AUDIO_SUFFIXES:
            raise ValueError(f"Unsupported audio format. Allowed: {', '.join(sorted(ALLOWED_AUDIO_SUFFIXES))}.")
        try:
            audio_bytes = base64.b64decode(encoded_audio, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("Audio payload is not valid base64.") from exc
        if not audio_bytes:
            raise ValueError("Audio file is empty.")
        if len(audio_bytes) > settings.max_upload_bytes:
            raise ValueError(f"Audio exceeds the {settings.max_upload_mb} MB limit.")
        with tempfile.TemporaryDirectory(prefix="scamtrace_upload_") as temp_dir:
            audio_path = Path(temp_dir) / f"upload{suffix}"
            audio_path.write_bytes(audio_bytes)
            voice = self.voice.analyze(audio_path) if settings.enable_voice_auth else {
                "synthetic_score": 0.0, "label": "uncertain", "confidence": 0.0,
                "model": "disabled", "available": False, "warning": "Voice analysis disabled.",
            }
            transcription = self.asr.transcribe(audio_path, language)
            result = self.analyze_text(
                transcription["text"], transcription.get("language", language),
                transcription.get("segments"), source="AUDIO_UPLOAD", voice=voice,
            )
            result["transcript"]["engine"] = transcription.get("engine", "local ASR")
            result["transcript"]["raw_text"] = transcription.get("raw_text", result["transcript"]["raw_text"])
            result["transcript"]["corrections"] = transcription.get("corrections", result["transcript"]["corrections"])
            return result

    def report(self, result: dict[str, Any], include_sensitive_evidence: bool = False) -> dict[str, Any]:
        return incident_report(result, include_sensitive_evidence=include_sensitive_evidence)

    def record_feedback(
        self,
        analysis_id: str,
        outcome: str,
        language: str,
        threat_level: str,
        threat_score: object,
    ) -> dict[str, Any]:
        if not settings.enable_feedback:
            raise RuntimeError("Local feedback is disabled by configuration.")
        receipt = self.feedback.record(analysis_id, outcome, language, threat_level, threat_score)
        logger.info(json.dumps({
            "event": "feedback_recorded",
            "outcome": str(outcome).upper(),
            "threat_level": str(threat_level).upper(),
        }))
        return receipt

    def _load_scenarios(self) -> list[dict[str, Any]]:
        source = settings.root / "data" / "demo" / "scenarios.json"
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("Scenario file must contain an array.")
            return data
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.error(f"demo_scenarios_unavailable: {exc}")
            return []

    @staticmethod
    def _validate_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = []
        for item in segments[:500]:
            text, _ = normalize_security_terms(str(item.get("text", "")).strip())
            if not text:
                continue
            start = max(0.0, float(item.get("start", 0)))
            end = max(start, float(item.get("end", start + 1)))
            validated.append({"start": round(start, 2), "end": round(end, 2), "text": text[:10000]})
        return validated or text_segments("")

    @staticmethod
    def _privacy() -> dict[str, str]:
        return {
            "audio_processing": "LOCAL",
            "speech_recognition": "LOCAL (when model installed)",
            "ai_inference": "LOCAL",
            "cloud_api_calls": "NONE",
            "raw_audio_uploaded": "NO — processed in an ephemeral local directory",
            "transcript_persistence": "OFF by default",
            "feedback_persistence": "OFF — explicit feedback stays only in local memory until exit",
        }
