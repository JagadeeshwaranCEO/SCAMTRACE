#!/usr/bin/env python3
"""Exercise SCAMTRACE's behavioural decision contracts, not field accuracy."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import ROOT
from backend.service import ScamTraceService


def main() -> None:
    rows = [
        json.loads(line)
        for line in (ROOT / "data" / "evaluation" / "decision_contracts.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    service = ScamTraceService()
    cases = []
    for row in rows:
        output = service.analyze_text(row["text"], row["language"], source="DECISION_CONTRACT")
        path = (output.get("narrative", {}).get("top_path") or {}).get("id")
        passed = output["fusion"]["level"] == row["expected_level"] and path == row["expected_path"]
        cases.append({
            "id": row["id"],
            "label": row["label"],
            "expected_level": row["expected_level"],
            "observed_level": output["fusion"]["level"],
            "expected_path": row["expected_path"],
            "observed_path": path,
            "counterfactual_present": bool(output.get("intervention", {}).get("counterfactual")),
            "passed": passed,
        })
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "name": "SCAMTRACE Behavioural Decision Contract Suite",
        "scope": "Deterministic safety and playbook contracts. This is not independent evaluation, field accuracy, or a model benchmark.",
        "cases": cases,
        "passed": sum(case["passed"] for case in cases),
        "total": len(cases),
    }
    report["status"] = "pass" if report["passed"] == report["total"] else "fail"
    (ROOT / "reports" / "decision_contracts.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# SCAMTRACE Behavioural Decision Contracts",
        "",
        f"Generated: {report['generated_at']}",
        "",
        report["scope"],
        "",
        f"## Result: {report['status'].upper()} — {report['passed']} / {report['total']}",
        "",
        "| Case | Expected level | Observed level | Expected path | Observed path | Counterfactual | Result |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in cases:
        lines.append(
            f"| {case['label']} | {case['expected_level']} | {case['observed_level']} | "
            f"{case['expected_path'] or 'none'} | {case['observed_path'] or 'none'} | "
            f"{'yes' if case['counterfactual_present'] else 'no'} | {'PASS' if case['passed'] else 'FAIL'} |"
        )
    (ROOT / "reports" / "decision_contracts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "passed": report["passed"], "total": report["total"]}, indent=2))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
