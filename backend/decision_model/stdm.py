"""STDM-1: a small, inspectable conversational threat decision model.

The model is deliberately bounded. It produces a distribution across attack
states from local language and evidence features; it does not generate text,
identify a caller, or make a legal finding.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from backend.config import settings
from backend.utils.text import normalize_text


MODEL_PATH = settings.root / "models" / "stdm_1.json"
LABELS = (
    "NORMAL",
    "SUSPICIOUS",
    "IMPERSONATION",
    "MANIPULATION",
    "CREDENTIAL_EXTRACTION",
    "FINANCIAL_EXTRACTION",
)
WORD_PATTERN = re.compile(r"[\w\u0900-\u097F\u0B80-\u0BFF]+", flags=re.UNICODE)


def _softmax(values: dict[str, float], temperature: float) -> dict[str, float]:
    temperature = max(0.25, temperature)
    maximum = max(values.values())
    weighted = {label: math.exp((value - maximum) / temperature) for label, value in values.items()}
    total = sum(weighted.values())
    return {label: value / total for label, value in weighted.items()}


def decision_features(
    text: str,
    language: str,
    tactics: list[dict[str, Any]],
    progression: dict[str, Any],
    classifier: dict[str, Any],
) -> list[str]:
    """Build a reviewable feature vector from local evidence."""
    words = [word for word in WORD_PATTERN.findall(normalize_text(text)) if len(word) > 1]
    features = [f"text:{word}" for word in words]
    features.extend(f"phrase:{left}__{right}" for left, right in zip(words, words[1:]))
    features.append(f"language:{language}")
    features.append(f"language_signal:{classifier.get('label', 'uncertain')}")
    score = float(classifier.get("scam_score", 0.5))
    features.append(f"language_score_bin:{min(9, max(0, int(score * 10)))}")
    momentum = float(progression.get("momentum", 0))
    features.append(f"momentum_bin:{min(9, max(0, int(momentum // 10)))}")
    features.append(f"progression:{progression.get('current_state', 'NORMAL')}")
    normalized = normalize_text(text)
    secret_terms = ("otp", "pin", "cvv", "password", "ओटीपी", "पिन", "पासवर्ड", "ஓடிபி", "பின்")
    protective_markers = (
        "never share", "do not share", "official app", "official website", "verify independently",
        "police have warned", "न बताएं", "मत बताएं", "அறிமுகமில்லாத", "mat batao",
    )
    if any(marker in normalized for marker in protective_markers):
        features.append("intent:protective_guidance")
    if any(term in normalized for term in secret_terms) and any(
        marker in normalized for marker in ("never", "do not", "न बताएं", "मत बताएं", "mat batao", "அறிமுகமில்லாத")
    ):
        features.append("intent:protective_secret_advice")
    if any(marker in normalized for marker in ("routine", "convenient", "scheduled", "at your time", "வசதியான", "सुविधा", "apne time")):
        features.append("intent:routine_service")
    for tactic in tactics:
        features.append(f"tactic:{tactic.get('tactic', 'UNKNOWN')}")
        features.append(f"tactic_occurrences:{tactic.get('tactic', 'UNKNOWN')}:{min(3, int(tactic.get('occurrences', 1)))}")
    return features


def train_stdm(
    rows: Iterable[dict[str, Any]],
    output_path: Path = MODEL_PATH,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Train a multiclass multinomial Naive Bayes state-decision model."""
    cleaned = [row for row in rows if str(row.get("state", "")) in LABELS and str(row.get("text", "")).strip()]
    class_counts = Counter(str(row["state"]) for row in cleaned)
    if len(class_counts) != len(LABELS):
        missing = sorted(set(LABELS) - set(class_counts))
        raise ValueError(f"STDM training data must contain every state; missing {missing}")
    feature_counts = {label: Counter() for label in LABELS}
    vocabulary = Counter()
    for row in cleaned:
        values = decision_features(
            str(row["text"]),
            str(row.get("language", "auto")),
            list(row.get("tactics", [])),
            dict(row.get("progression", {})),
            dict(row.get("classifier", {})),
        )
        feature_counts[str(row["state"])].update(values)
        vocabulary.update(values)
    retained = {item for item, count in vocabulary.items() if count >= 2}
    alpha = 0.8
    size = max(1, len(retained))
    denominators = {
        label: sum(count for item, count in feature_counts[label].items() if item in retained) + alpha * size
        for label in LABELS
    }
    model = {
        "format": "scamtrace-stdm-v1",
        "model_name": "STDM-1 — SCAMTRACE Threat Decision Model",
        "version": "2026.09.21",
        "algorithm": "calibrated multiclass multinomial naive bayes over local evidence features",
        "labels": list(LABELS),
        "class_counts": dict(class_counts),
        "vocabulary_size": len(retained),
        "alpha": alpha,
        "priors": {label: math.log(class_counts[label] / len(cleaned)) for label in LABELS},
        "feature_log_probabilities": {
            label: {
                item: round(math.log((feature_counts[label][item] + alpha) / denominators[label]), 8)
                for item in retained
            }
            for label in LABELS
        },
        "unknown_feature_log_probability": {
            label: round(math.log(alpha / denominators[label]), 8) for label in LABELS
        },
        "calibration": {"temperature": 1.0, "method": "unfitted"},
        "metadata": metadata or {},
        "notes": "Decision-support state distribution. Do not present as a criminality or scam probability.",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    return model


def raw_logits(model: dict[str, Any], features: list[str]) -> dict[str, float]:
    counts = Counter(features)
    logits: dict[str, float] = {}
    for label in model["labels"]:
        values = model["feature_log_probabilities"][label]
        unknown = float(model["unknown_feature_log_probability"][label])
        logits[label] = float(model["priors"][label]) + sum(
            count * float(values.get(feature, unknown)) for feature, count in counts.items()
        )
    return logits


def predict_stdm(model: dict[str, Any], features: list[str]) -> dict[str, Any]:
    logits = raw_logits(model, features)
    temperature = float(model.get("calibration", {}).get("temperature", 1.0))
    distribution = _softmax(logits, temperature)
    state, confidence = max(distribution.items(), key=lambda item: item[1])
    uncertainty = "HIGH" if confidence < 0.52 else "MEDIUM" if confidence < 0.72 else "LOW"
    rounded_distribution = {label: round(distribution[label], 4) for label in model["labels"]}
    # Preserve a proper probability simplex after presentation rounding.
    rounded_distribution[state] = round(rounded_distribution[state] + (1.0 - sum(rounded_distribution.values())), 4)
    return {
        "current_attack_state": state,
        "risk_distribution": rounded_distribution,
        "confidence": round(confidence, 4),
        "uncertainty": uncertainty,
        "model": model["model_name"],
        "model_version": model["version"],
        "calibration": model.get("calibration", {}),
        "note": "STDM-1 is an additional decision-support signal. The evidence fusion engine remains the intervention authority.",
    }


def calibrate_stdm(model: dict[str, Any], rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Choose temperature on validation NLL without changing class rankings."""
    prepared = []
    for row in rows:
        features = list(row["features"])
        prepared.append((raw_logits(model, features), str(row["state"])))
    if not prepared:
        return model
    best: tuple[float, float] | None = None
    for temperature in (0.5, 0.65, 0.8, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0):
        loss = 0.0
        for logits, actual in prepared:
            probability = max(1e-8, _softmax(logits, temperature)[actual])
            loss -= math.log(probability)
        candidate = (loss / len(prepared), temperature)
        if best is None or candidate < best:
            best = candidate
    assert best is not None
    model["calibration"] = {
        "temperature": best[1],
        "method": "held-out temperature scaling by multiclass negative log likelihood",
        "validation_rows": len(prepared),
        "negative_log_likelihood": round(best[0], 5),
    }
    return model


class StdmDecisionModel:
    """Fail-safe local adapter for a JSON STDM-1 artifact."""

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        self.model_path = model_path
        self.model: dict[str, Any] | None = None
        self.load_error: str | None = None
        self.load()

    @property
    def available(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        try:
            data = json.loads(self.model_path.read_text(encoding="utf-8"))
            if data.get("format") != "scamtrace-stdm-v1":
                raise ValueError("unsupported STDM model format")
            self.model = data
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.model = None
            self.load_error = f"STDM-1 unavailable: {exc}"

    def status(self) -> dict[str, Any]:
        if not self.model:
            return {"available": False, "deployment_mode": "UNAVAILABLE", "warning": self.load_error}
        metadata = self.model.get("metadata", {})
        metrics = metadata.get("development_metrics", {})
        return {
            "available": True,
            "model": self.model["model_name"],
            "deployment_mode": "SHADOW_ONLY",
            "reason": "Current artifact was trained on authored synthetic contrast data and has not passed independent real-call calibration validation.",
            "development_metrics": {
                "state_accuracy": metrics.get("state_accuracy"),
                "expected_calibration_error": metrics.get("expected_calibration_error"),
                "multiclass_brier_score": metrics.get("multiclass_brier_score"),
            },
        }

    def predict(
        self,
        text: str,
        language: str,
        tactics: list[dict[str, Any]],
        progression: dict[str, Any],
        classifier: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.model:
            return {
                "available": False,
                "current_attack_state": "UNAVAILABLE",
                "risk_distribution": {},
                "confidence": 0.0,
                "uncertainty": "HIGH",
                "warning": self.load_error,
            }
        result = predict_stdm(self.model, decision_features(text, language, tactics, progression, classifier))
        result.update({
            "available": True,
            "deployment_mode": "SHADOW_ONLY",
            "warning": "Experimental model-development signal. It does not change alerts until independently validated on real, consented conversation data.",
        })
        return result
