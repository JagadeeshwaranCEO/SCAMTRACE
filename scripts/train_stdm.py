#!/usr/bin/env python3
"""Train STDM-1 from local conversation-state contrast records."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.attack_engine.progression import build_progression
from backend.classifiers.scam_classifier import ScamLanguageClassifier
from backend.classifiers.taxonomy import detect_tactics
from backend.decision_model.stdm import LABELS, calibrate_stdm, decision_features, predict_stdm, train_stdm
from backend.utils.text import detect_language, text_segments

DEFAULT_DATASET = ROOT / "data" / "processed" / "stdm_synthetic_contrasts.jsonl"
MODEL_PATH = ROOT / "models" / "stdm_1.json"


def load_rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prepare_rows(rows: list[dict[str, Any]], classifier: ScamLanguageClassifier) -> list[dict[str, Any]]:
    prepared = []
    for row in rows:
        language = detect_language(str(row["text"]), str(row.get("language", "auto")))
        segments = text_segments(str(row["text"]))
        by_segment = [detect_tactics(item["text"]) for item in segments]
        tactics = []
        seen = set()
        for entries in by_segment:
            for item in entries:
                if item["tactic"] not in seen:
                    tactics.append(item)
                    seen.add(item["tactic"])
        progression = build_progression(segments, by_segment)
        language_signal = classifier.predict(str(row["text"]))
        prepared.append({
            **row,
            "language": language,
            "tactics": tactics,
            "progression": progression,
            "classifier": language_signal,
            "features": decision_features(str(row["text"]), language, tactics, progression, language_signal),
        })
    return prepared


def group_split(rows: list[dict[str, Any]], fraction: float = 0.25) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row["family"])].append(row)
    by_state: dict[str, list[tuple[str, list[dict[str, Any]]]]] = defaultdict(list)
    for family, items in groups.items():
        by_state[str(items[0]["state"])].append((family, items))
    train, validation = [], []
    for state in LABELS:
        ordered = sorted(
            by_state[state],
            key=lambda pair: hashlib.blake2b(pair[0].encode(), digest_size=8).hexdigest(),
        )
        count = max(1, round(len(ordered) * fraction))
        for _, items in ordered[:count]:
            validation.extend(items)
        for _, items in ordered[count:]:
            train.extend(items)
    return train, validation


def metrics(rows: list[dict[str, Any]], model: dict[str, Any]) -> dict[str, Any]:
    matrix = Counter()
    brier_total = 0.0
    bins: list[list[float]] = [[] for _ in range(10)]
    correct: list[list[int]] = [[] for _ in range(10)]
    for row in rows:
        result = predict_stdm(model, list(row["features"]))
        actual = str(row["state"])
        predicted = result["current_attack_state"]
        matrix[(actual, predicted)] += 1
        distribution = result["risk_distribution"]
        brier_total += sum((distribution[label] - (1.0 if label == actual else 0.0)) ** 2 for label in LABELS)
        bucket = min(9, int(result["confidence"] * 10))
        bins[bucket].append(result["confidence"])
        correct[bucket].append(1 if predicted == actual else 0)
    per_label = []
    for label in LABELS:
        tp = matrix[(label, label)]
        fp = sum(matrix[(other, label)] for other in LABELS if other != label)
        fn = sum(matrix[(label, other)] for other in LABELS if other != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        per_label.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    ece = 0.0
    reliability = []
    for index, values in enumerate(bins):
        if values:
            observed = sum(correct[index]) / len(values)
            average_confidence = sum(values) / len(values)
            ece += len(values) / len(rows) * abs(observed - average_confidence)
            reliability.append({"bin": index, "n": len(values), "confidence": round(average_confidence, 4), "accuracy": round(observed, 4)})
    total = len(rows)
    return {
        "n": total,
        "state_accuracy": round(sum(matrix[(label, label)] for label in LABELS) / total, 4),
        "macro_f1": round(sum(per_label) / len(per_label), 4),
        "multiclass_brier_score": round(brier_total / total, 5),
        "expected_calibration_error": round(ece, 5),
        "reliability_bins": reliability,
        "confusion_matrix": {actual: {predicted: matrix[(actual, predicted)] for predicted in LABELS} for actual in LABELS},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    args = parser.parse_args()
    if not args.dataset.exists():
        raise SystemExit(f"Dataset unavailable: {args.dataset}. Run scripts/generate_stdm_dataset.py first.")
    raw_rows = load_rows(args.dataset)
    if {row.get("state") for row in raw_rows} != set(LABELS):
        raise SystemExit("Dataset must contain every STDM state.")
    classifier = ScamLanguageClassifier()
    if not classifier.available:
        raise SystemExit(f"Language baseline unavailable: {classifier.load_error}")
    rows = prepare_rows(raw_rows, classifier)
    train_rows, validation_rows = group_split(rows)
    metadata = {
        "trained_at": datetime.now(UTC).isoformat(),
        "source": str(args.dataset.relative_to(ROOT)),
        "provenance": "authored synthetic contrast data for model development",
        "split": "deterministic family-group split; template variants remain together",
        "training_rows": len(train_rows),
        "validation_rows": len(validation_rows),
    }
    model = train_stdm(train_rows, MODEL_PATH, metadata)
    model = calibrate_stdm(model, validation_rows)
    result = metrics(validation_rows, model)
    model["metadata"]["development_metrics"] = result
    MODEL_PATH.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {
        "generated_at": metadata["trained_at"],
        "model": {"name": model["model_name"], "algorithm": model["algorithm"], "vocabulary_size": model["vocabulary_size"]},
        "data": {**metadata, "state_distribution": dict(Counter(row["state"] for row in raw_rows))},
        "calibration": model["calibration"],
        "development_metrics": result,
        "critical_limit": "Synthetic authored contrast development data only. These results are not independent evaluation, real-call accuracy, or a deployment calibration claim.",
    }
    (ROOT / "reports" / "stdm_training.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# STDM-1 Model Development Report", "", f"Generated: {report['generated_at']}", "",
        "## Scope", "", report["critical_limit"], "", "## Data", "",
        f"- Source: {metadata['source']}",
        f"- State distribution: {report['data']['state_distribution']}",
        f"- Split: {metadata['split']}",
        "", "## Results", "",
        f"- State accuracy: {result['state_accuracy']:.2%}",
        f"- Macro F1: {result['macro_f1']:.2%}",
        f"- Multiclass Brier score: {result['multiclass_brier_score']:.5f}",
        f"- Expected Calibration Error: {result['expected_calibration_error']:.5f}",
        "", "## Reliability bins", "",
        "| Bin | N | Mean confidence | Observed accuracy |",
        "| ---: | ---: | ---: | ---: |",
        *[f"| {item['bin']} | {item['n']} | {item['confidence']:.2%} | {item['accuracy']:.2%} |" for item in result["reliability_bins"]],
    ]
    (ROOT / "reports" / "stdm_training.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
