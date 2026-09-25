#!/usr/bin/env python3
"""Evaluate Hindi and Tamil behavior on an authored, train-excluded holdout."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.service import ScamTraceService


DATASET = ROOT / "data" / "evaluation" / "multilingual_holdout_v1.jsonl"


def binary_metrics(values: list[tuple[bool, bool]]) -> dict[str, Any]:
    matrix = Counter()
    for predicted, actual in values:
        matrix["tp" if predicted and actual else "tn" if not predicted and not actual else "fp" if predicted else "fn"] += 1
    tp, tn, fp, fn = (matrix[key] for key in ("tp", "tn", "fp", "fn"))
    total = len(values)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "n": total,
        "accuracy": round((tp + tn) / total, 4) if total else 0.0,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "balanced_accuracy": round((recall + specificity) / 2, 4),
        "false_positive_rate": round(fp / (fp + tn), 4) if fp + tn else 0.0,
        "false_negative_rate": round(fn / (fn + tp), 4) if fn + tp else 0.0,
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
    }


def main() -> None:
    rows = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line.strip()]
    service = ScamTraceService()
    predictions: dict[str, dict[str, list[tuple[bool, bool]]]] = defaultdict(lambda: defaultdict(list))
    cases = []
    for row in rows:
        output = service.analyze_text(row["text"], row["language"])
        actual = row["label"] == "scam"
        # Use the deployed classifier contract (>=0.60 => scam_language), not
        # an analysis-only 0.50 ranking threshold.
        classifier_positive = output["classifier"]["label"] == "scam_language"
        full_positive = output["fusion"]["score"] >= 24
        predictions[row["language"]]["classifier"].append((classifier_positive, actual))
        predictions[row["language"]]["full_scamtrace"].append((full_positive, actual))
        predictions["overall"]["classifier"].append((classifier_positive, actual))
        predictions["overall"]["full_scamtrace"].append((full_positive, actual))
        cases.append({
            "id": row["id"],
            "actual": row["label"],
            "language": row["language"],
            "classifier_score": output["classifier"]["scam_score"],
            "classifier_label": output["classifier"]["label"],
            "threat_score": output["fusion"]["score"],
            "threat_level": output["fusion"]["level"],
            "tactics": [item["tactic"] for item in output["tactics"]],
        })
    metrics = {
        language: {system: binary_metrics(values) for system, values in systems.items()}
        for language, systems in sorted(predictions.items())
    }
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": {
            "name": "SCAMTRACE Hindi/Tamil authored holdout v1",
            "path": str(DATASET.relative_to(ROOT)),
            "rows": len(rows),
            "class_distribution": dict(Counter(row["label"] for row in rows)),
            "language_distribution": dict(Counter(row["language"] for row in rows)),
            "training_exclusion": "These exact rows are not loaded by scripts/train_scam_classifier.py.",
            "limit": "Authored regression holdout, not independent real-call accuracy or population calibration.",
        },
        "metrics": metrics,
        "cases": cases,
    }
    (ROOT / "reports" / "multilingual_evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# SCAMTRACE Hindi/Tamil Evaluation", "", f"Generated: {report['generated_at']}", "",
        "## Scope", "", report["dataset"]["training_exclusion"], "", report["dataset"]["limit"], "",
        "## Results", "", "| Language | System | N | Accuracy | Precision | Recall | F1 | FPR | FNR |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for language, systems in metrics.items():
        for system, value in systems.items():
            lines.append(
                f"| {language} | {system.replace('_', ' ')} | {value['n']} | {value['accuracy']:.2%} | "
                f"{value['precision']:.2%} | {value['recall']:.2%} | {value['f1']:.2%} | "
                f"{value['false_positive_rate']:.2%} | {value['false_negative_rate']:.2%} |"
            )
    lines.extend(["", "## Limit", "", report["dataset"]["limit"]])
    (ROOT / "reports" / "multilingual_evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
