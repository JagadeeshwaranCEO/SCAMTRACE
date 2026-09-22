#!/usr/bin/env python3
"""Run the deterministic SCAMTRACE demo suite from a terminal."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.service import ScamTraceService


def main() -> None:
    service = ScamTraceService()
    print("SCAMTRACE demo verification")
    for scenario in service.scenarios:
        output = service.analyze_scenario(scenario["id"])
        tactics = ", ".join(item["tactic"] for item in output["tactics"]) or "none"
        print(f"- {scenario['name']}: {output['fusion']['level']} {output['fusion']['score']}/100 | {tactics}")


if __name__ == "__main__":
    main()

