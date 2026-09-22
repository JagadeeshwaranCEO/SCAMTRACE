#!/usr/bin/env python3
"""Run transparent component and end-to-end metrics on curated regression cases."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import ROOT
from backend.service import ScamTraceService


def metrics(predictions: list[tuple[bool, bool]]) -> dict[str, float | int]:
    tp = sum(pred and actual for pred, actual in predictions)
    tn = sum(not pred and not actual for pred, actual in predictions)
    fp = sum(pred and not actual for pred, actual in predictions)
    fn = sum(not pred and actual for pred, actual in predictions)
    total = len(predictions)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "n": total, "accuracy": round((tp + tn) / total, 4) if total else 0.0,
        "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
        "false_positive_rate": round(fp / (fp + tn), 4) if fp + tn else 0.0,
        "false_negative_rate": round(fn / (fn + tp), 4) if fn + tp else 0.0,
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
    }


def main() -> None:
    if not (ROOT / "models" / "scam_classifier.json").exists():
        from scripts.train_scam_classifier import main as train
        train()
    rows = [json.loads(line) for line in (ROOT / "data" / "evaluation" / "curated_eval.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    service = ScamTraceService()
    systems: dict[str, list[tuple[bool, bool]]] = {
        "rule_engine_only": [], "classifier_only": [], "attack_engine_only": [],
        "classifier_plus_attack_engine": [], "full_scamtrace": [], "full_plus_voice_signal": [],
    }
    per_case: list[dict[str, Any]] = []
    for row in rows:
        output = service.analyze_text(row["text"], row["language"])
        actual = row["label"] == "scam"
        rule = bool(output["tactics"])
        classifier = output["classifier"]["scam_score"] >= 0.5
        attack = output["progression"]["momentum"] >= 24
        full = output["fusion"]["score"] >= 24
        # No synthetic-audio claim is used in this corpus. This row keeps the
        # ablation schema stable; it is equal to Full until a labelled voice set
        # is supplied and separately documented.
        full_voice = full
        values = [rule, classifier, attack, classifier or attack, full, full_voice]
        for key, prediction in zip(systems, values):
            systems[key].append((prediction, actual))
        per_case.append({
            "id": row["id"], "actual": row["label"], "predicted_level": output["fusion"]["level"],
            "score": output["fusion"]["score"], "tactics": [item["tactic"] for item in output["tactics"]],
        })
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": {
            "name": "SCAMTRACE curated multilingual regression set",
            "rows": len(rows),
            "class_distribution": dict(Counter(row["label"] for row in rows)),
            "important_limit": "This is a small hand-curated regression suite used to exercise tactic coverage. It is not an independent held-out evaluation or representative real-world benchmark.",
        },
        "metrics": {name: metrics(items) for name, items in systems.items()},
        "cases": per_case,
        "voice_ablation_note": "No external voice dataset has been incorporated yet, so Full + Voice is intentionally identical to Full. No voice metric is claimed.",
    }
    report_path = ROOT / "reports" / "evaluation.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = ["# SCAMTRACE Regression Evaluation", "", f"Generated: {report['generated_at']}", "", "## Scope", "", report["dataset"]["important_limit"], "", "## Results", "", "| System | Accuracy | Precision | Recall | F1 | FPR | FNR |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for name, value in report["metrics"].items():
        markdown.append(f"| {name.replace('_', ' ')} | {value['accuracy']:.2%} | {value['precision']:.2%} | {value['recall']:.2%} | {value['f1']:.2%} | {value['false_positive_rate']:.2%} | {value['false_negative_rate']:.2%} |")
    markdown.extend(["", "## Voice ablation", "", report["voice_ablation_note"], "", "## Confusion matrix", ""])
    for name, value in report["metrics"].items():
        matrix = value["confusion_matrix"]
        markdown.append(f"- {name}: TP {matrix['tp']}, TN {matrix['tn']}, FP {matrix['fp']}, FN {matrix['fn']}")
    (ROOT / "reports" / "evaluation.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(json.dumps(report["metrics"]["full_scamtrace"], indent=2))
    print(f"Wrote {report_path} and reports/evaluation.md")


if __name__ == "__main__":
    main()
