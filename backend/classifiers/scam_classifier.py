"""Safe, locally trained multilingual social-engineering language classifier."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from backend.config import settings
from backend.utils.text import normalize_text


MODEL_PATH = settings.root / "models" / "scam_classifier.json"
WORD_PATTERN = re.compile(r"[\w\u0900-\u097F\u0B80-\u0BFF]+", flags=re.UNICODE)


def tokens(text: str) -> list[str]:
    """Backward-compatible word and phrase features."""
    words = WORD_PATTERN.findall(normalize_text(text))
    unigrams = [word for word in words if len(word) > 1]
    bigrams = [f"{left}__{right}" for left, right in zip(unigrams, unigrams[1:])]
    return unigrams + bigrams


def features(text: str, config: dict[str, Any] | None = None) -> list[str]:
    """Extract auditable character features for code-mixed speech."""
    config = config or {}
    feature_list = tokens(text)
    if not config.get("char_ngrams", False):
        return feature_list
    compact = re.sub(r"\s+", " ", normalize_text(text))
    min_n = int(config.get("char_min", 3))
    max_n = int(config.get("char_max", 4))
    for size in range(min_n, max_n + 1):
        if len(compact) >= size:
            feature_list.extend(f"char:{compact[index:index + size]}" for index in range(len(compact) - size + 1))
    return feature_list


def _sigmoid(value: float) -> float:
    value = max(-30.0, min(30.0, value))
    return 1.0 / (1.0 + math.exp(-value))


def raw_score(model: dict[str, Any], text: str) -> tuple[float, list[tuple[str, float]]]:
    """Return a model logit and feature contributions for safe JSON artifacts."""
    vocabulary = model.get("log_odds") or model.get("weights") or {}
    counts = Counter(features(text, model.get("feature_config")))
    raw = float(model["intercept"])
    matched: list[tuple[str, float]] = []
    for feature, count in counts.items():
        weight = vocabulary.get(feature)
        if weight is not None:
            value = min(2.0, math.log1p(count)) if model.get("format") == "scamtrace-logreg-v1" else min(2, count)
            contribution = float(weight) * value
            raw += contribution
            matched.append((feature, contribution))
    return raw, matched


def predict_model(model: dict[str, Any], text: str) -> dict[str, Any]:
    raw, matched = raw_score(model, text)
    vocabulary = model.get("log_odds") or model.get("weights") or {}
    observed_features = set(features(text, model.get("feature_config")))
    observed_word_phrase = {feature for feature in observed_features if not feature.startswith("char:")}
    known_word_phrase = {feature for feature in observed_word_phrase if feature in vocabulary}
    calibration = model.get("calibration", {})
    temperature = max(0.25, float(calibration.get("temperature", 1.0)))
    bias = float(calibration.get("bias", 0.0))
    scam_score = _sigmoid((raw + bias) / temperature)
    confidence = min(0.94, 0.25 + abs(scam_score - 0.5) * 0.9 + min(1.0, len(matched) / 12) * 0.25)
    label = "scam_language" if scam_score >= 0.60 else "benign_language" if scam_score <= 0.40 else "uncertain"
    return {
        "scam_score": round(scam_score, 4),
        "label": label,
        "confidence": round(confidence, 3),
        "model": model.get("model_name", "SCAMTRACE language baseline"),
        "model_version": model.get("version", "unknown"),
        "top_features": [
            {
                "feature": feature.replace("char:", "").replace("__", " "),
                "direction": "scam" if weight > 0 else "benign",
                "weight": round(weight, 3),
            }
            for feature, weight in sorted(matched, key=lambda item: abs(item[1]), reverse=True)
            if not feature.startswith("char:")
        ][:6],
        # This intentionally exposes only counts and ratios. It is consumed by
        # the local drift monitor and cannot be used to reconstruct text.
        "feature_coverage": {
            "observed_word_phrase_features": len(observed_word_phrase),
            "known_word_phrase_features": len(known_word_phrase),
            "known_word_phrase_ratio": round(len(known_word_phrase) / max(1, len(observed_word_phrase)), 4),
        },
    }


class ScamLanguageClassifier:
    """Small, auditable classifier with fail-safe neutral output."""

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        self.model_path = model_path
        self.model: dict[str, Any] | None = None
        self.load_error: str | None = None
        self.load()

    def load(self) -> None:
        try:
            if self.model_path.exists():
                data = json.loads(self.model_path.read_text(encoding="utf-8"))
                if data.get("format") not in {"scamtrace-mnb-v1", "scamtrace-mnb-v2", "scamtrace-logreg-v1"}:
                    raise ValueError("unsupported model format")
                self.model = data
            else:
                self.load_error = "Model artifact not found. Run scripts/train_scam_classifier.py."
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.load_error = f"Could not load classifier artifact: {exc}"
            self.model = None

    @property
    def available(self) -> bool:
        return self.model is not None

    def predict(self, text: str) -> dict[str, Any]:
        if not self.model:
            return {
                "scam_score": 0.5, "label": "uncertain", "confidence": 0.0,
                "model": "unavailable", "warning": self.load_error, "top_features": [],
            }
        return predict_model(self.model, text)


def train_model(
    rows: Iterable[dict[str, Any]],
    output_path: Path | None = MODEL_PATH,
    feature_config: dict[str, Any] | None = None,
    min_feature_count: int = 1,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Train a safe JSON multinomial NB classifier from labelled text rows."""
    feature_config = feature_config or {"char_ngrams": True, "char_min": 3, "char_max": 4}
    cleaned = [
        {"text": str(row["text"]), "label": str(row["label"]).lower()}
        for row in rows
        if str(row.get("label", "")).lower() in {"scam", "benign"} and str(row.get("text", "")).strip()
    ]
    class_counts = Counter(row["label"] for row in cleaned)
    if not class_counts["scam"] or not class_counts["benign"]:
        raise ValueError("training data must contain scam and benign labels")
    class_feature_counts = {"scam": Counter(), "benign": Counter()}
    global_counts = Counter()
    for row in cleaned:
        row_features = features(row["text"], feature_config)
        class_feature_counts[row["label"]].update(row_features)
        global_counts.update(row_features)
    vocabulary = {feature for feature, count in global_counts.items() if count >= min_feature_count}
    alpha = 0.65
    total_scam = sum(count for feature, count in class_feature_counts["scam"].items() if feature in vocabulary)
    total_benign = sum(count for feature, count in class_feature_counts["benign"].items() if feature in vocabulary)
    vocab_size = max(1, len(vocabulary))
    log_odds = {}
    for feature in vocabulary:
        scam_probability = (class_feature_counts["scam"][feature] + alpha) / (total_scam + alpha * vocab_size)
        benign_probability = (class_feature_counts["benign"][feature] + alpha) / (total_benign + alpha * vocab_size)
        log_odds[feature] = round(math.log(scam_probability / benign_probability), 6)
    prior = class_counts["scam"] / len(cleaned)
    model = {
        "format": "scamtrace-mnb-v2",
        "model_name": "SCAMTRACE Multilingual Social-Engineering Baseline",
        "version": "2026.09.21-realdata-v1",
        "algorithm": "calibrated multinomial naive bayes (word + phrase + character n-gram features)",
        "training_rows": len(cleaned),
        "class_distribution": dict(class_counts),
        "feature_config": feature_config,
        "min_feature_count": min_feature_count,
        "intercept": round(math.log(prior / (1 - prior)), 6),
        "log_odds": log_odds,
        "calibration": {"temperature": 1.0, "bias": 0.0, "method": "unfitted"},
        "metadata": dict(metadata or {}),
        "notes": "Decision-support language signal. Not a population-calibrated fraud probability.",
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    return model


def train_logistic_model(
    rows: Iterable[dict[str, Any]],
    output_path: Path | None = MODEL_PATH,
    feature_config: dict[str, Any] | None = None,
    min_feature_count: int = 2,
    metadata: dict[str, Any] | None = None,
    epochs: int = 110,
    learning_rate: float = 0.16,
    l2: float = 0.0008,
) -> dict[str, Any]:
    """Train a class-balanced sparse logistic baseline using local features.

    The model is intentionally small and inspectable. Unlike the previous NB
    baseline, its optimisation rebalances per-class loss so duplicated scam
    templates cannot silently set the operating prior.
    """
    feature_config = feature_config or {"char_ngrams": True, "char_min": 3, "char_max": 4}
    cleaned = [
        {"text": str(row["text"]), "label": str(row["label"]).lower()}
        for row in rows
        if str(row.get("label", "")).lower() in {"scam", "benign"} and str(row.get("text", "")).strip()
    ]
    class_counts = Counter(row["label"] for row in cleaned)
    if not class_counts["scam"] or not class_counts["benign"]:
        raise ValueError("training data must contain scam and benign labels")
    document_counts: Counter[str] = Counter()
    prepared: list[tuple[Counter[str], int]] = []
    for row in cleaned:
        values = Counter(features(row["text"], feature_config))
        document_counts.update(values.keys())
        prepared.append((values, 1 if row["label"] == "scam" else 0))
    vocabulary = {feature for feature, count in document_counts.items() if count >= min_feature_count}
    weights = {feature: 0.0 for feature in vocabulary}
    intercept = 0.0
    # Each class has equal aggregate influence, regardless of template count.
    class_weight = {0: len(prepared) / (2 * class_counts["benign"]), 1: len(prepared) / (2 * class_counts["scam"])}
    ordered = sorted(prepared, key=lambda item: (item[1], tuple(sorted(item[0].keys()))))
    for epoch in range(epochs):
        rate = learning_rate / (1.0 + epoch * 0.035)
        for values, label in ordered:
            active = {feature: min(2.0, math.log1p(count)) for feature, count in values.items() if feature in vocabulary}
            logit = intercept + sum(weights[feature] * value for feature, value in active.items())
            error = (_sigmoid(logit) - label) * class_weight[label]
            intercept -= rate * error
            for feature, value in active.items():
                weights[feature] -= rate * (error * value + l2 * weights[feature])
    model = {
        "format": "scamtrace-logreg-v1",
        "model_name": "SCAMTRACE Robust Multilingual Language Baseline",
        "version": "2026.09.22-robust-v1",
        "algorithm": "class-balanced sparse logistic regression (word + phrase + character n-gram features)",
        "training_rows": len(cleaned),
        "class_distribution": dict(class_counts),
        "feature_config": feature_config,
        "min_feature_count": min_feature_count,
        "intercept": round(intercept, 8),
        "weights": {feature: round(weight, 8) for feature, weight in weights.items()},
        "calibration": {"temperature": 1.0, "bias": 0.0, "method": "unfitted"},
        "training": {
            "epochs": epochs,
            "learning_rate": learning_rate,
            "l2": l2,
            "class_balancing": "inverse-frequency per-class loss weighting",
        },
        "metadata": dict(metadata or {}),
        "notes": "Decision-support language signal. Not a population-calibrated fraud probability.",
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    return model


def calibrate_model(model: dict[str, Any], rows: Iterable[dict[str, Any]], class_balanced: bool = False) -> dict[str, Any]:
    """Fit a conservative temperature/bias pair using held-out labelled rows."""
    validation = [
        (raw_score(model, str(row["text"]))[0], 1 if str(row["label"]).lower() == "scam" else 0)
        for row in rows
    ]
    if not validation:
        return model
    label_counts = Counter(label for _, label in validation)
    weights = {
        label: len(validation) / (2 * label_counts[label]) if class_balanced and label_counts[label] else 1.0
        for label in (0, 1)
    }
    best: tuple[float, float, float] | None = None
    for temperature in (1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0, 24.0, 32.0):
        for bias in (-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0):
            loss = 0.0
            for raw, label in validation:
                probability = min(1 - 1e-8, max(1e-8, _sigmoid((raw + bias) / temperature)))
                loss += weights[label] * -(label * math.log(probability) + (1 - label) * math.log(1 - probability))
            candidate = (loss / sum(weights[label] for _, label in validation), temperature, bias)
            if best is None or candidate < best:
                best = candidate
    assert best is not None
    model["calibration"] = {
        "temperature": best[1], "bias": best[2],
        "method": "grid-search held-out class-balanced negative log likelihood" if class_balanced else "grid-search held-out negative log likelihood",
        "validation_rows": len(validation), "negative_log_likelihood": round(best[0], 5),
    }
    return model
