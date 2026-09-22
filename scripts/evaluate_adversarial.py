#!/usr/bin/env python3
"""Evaluate authored adversarial decision cases with actual local inference.

This is an internal red-team gate for paraphrase, regional-language,
code-switching, and ASR-noise scenarios. It deliberately does not claim field
accuracy, independent test-set performance, or prevalence-weighted error rate.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import ROOT
from backend.service import ScamTraceService


POSITIVE_LEVELS = {"HIGH", "CRITICAL"}


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(row["expected"] and row["observed"] for row in rows)
    fp = sum(not row["expected"] and row["observed"] for row in rows)
    tn = sum(not row["expected"] and not row["observed"] for row in rows)
    fn = sum(row["expected"] and not row["observed"] for row in rows)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0.0,
        "false_positive_rate": round(fp / (fp + tn), 4) if fp + tn else None,
        "false_negative_rate": round(fn / (fn + tp), 4) if fn + tp else None,
    }


def main() -> None:
    source = ROOT / "data" / "evaluation" / "adversarial_redteam_v1.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    service = ScamTraceService()
    cases: list[dict[str, Any]] = []
    for row in rows:
        output = service.analyze_text(row["text"], row["language"], source="ADVERSARIAL_EVALUATION")
        expected = row["label"] == "scam"
        observed = output["fusion"]["level"] in POSITIVE_LEVELS
        cases.append({
            "id": row["id"], "label": row["label"], "language": row["language"],
            "surface": row["surface"], "perturbation": row["perturbation"],
            "expected": expected, "observed": observed,
            "observed_level": output["fusion"]["level"],
            "top_path": (output.get("narrative", {}).get("top_path") or {}).get("id"),
        })
    groups: dict[str, dict[str, list[dict[str, Any]]]] = {"language": defaultdict(list), "surface": defaultdict(list), "perturbation": defaultdict(list)}
    for case in cases:
        for field, buckets in groups.items():
            buckets[case[field]].append(case)
    by_group = {field: {key: metrics(values) for key, values in sorted(buckets.items())} for field, buckets in groups.items()}
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "name": "SCAMTRACE adversarial decision evaluation v1",
        "dataset": "Internally authored red-team cases; 8 benign and 14 scam examples across paraphrase, ASR-noise, code-switching, and regional-language conditions.",
        "scope": "Measured local-engine decision outcomes. Not independent field evaluation, population calibration, model-only evaluation, or a claim of real-world prevalence.",
        "positive_decision": "HIGH or CRITICAL threat level",
        "overall": metrics(cases),
        "by_group": by_group,
        "cases": cases,
    }
    report["status"] = "pass" if not report["overall"]["confusion_matrix"]["fp"] and not report["overall"]["confusion_matrix"]["fn"] else "review_required"
    (ROOT / "reports" / "adversarial_evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# SCAMTRACE Adversarial Decision Evaluation v1", "", f"Generated: {report['generated_at']}", "",
        report["dataset"], "", report["scope"], "", f"## Result: {report['status'].upper()}", "",
        "| Metric | Value |", "| --- | ---: |",
    ]
    for key, value in report["overall"].items():
        lines.append(f"| {key.replace('_', ' ')} | {json.dumps(value) if isinstance(value, dict) else value} |")
    lines.extend(["", "## Case outcomes", "", "| ID | Label | Language | Perturbation | Level | Path | Correct decision |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for case in cases:
        lines.append(f"| {case['id']} | {case['label']} | {case['language']} | {case['perturbation']} | {case['observed_level']} | {case['top_path'] or 'none'} | {'yes' if case['expected'] == case['observed'] else 'no'} |")
    (ROOT / "reports" / "adversarial_evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["overall"]}, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
