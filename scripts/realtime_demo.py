"""Run the real-time SCAMTRACE engine against a scenario, segment by segment."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.service import ScamTraceService


def main() -> None:
    parser = argparse.ArgumentParser(description="Local incremental SCAMTRACE demo")
    parser.add_argument("--scenario", default="human_digital_arrest", help="Scenario identifier from data/demo/scenarios.json")
    args = parser.parse_args()

    service = ScamTraceService()
    scenario = next((item for item in service.scenarios if item["id"] == args.scenario), None)
    if not scenario:
        known = ", ".join(item["id"] for item in service.scenarios)
        raise SystemExit(f"Unknown scenario. Choose one of: {known}")

    started = service.realtime.start(scenario.get("language", "auto"))
    session_id = started["session_id"]
    print(json.dumps({key: value for key, value in started.items() if key != "session_id"}, ensure_ascii=False))
    print(f"Session: {session_id}")
    for item in scenario.get("segments") or []:
        result = service.realtime.ingest(
            session_id, item["text"], item.get("start"), item.get("end"), scenario.get("language", "auto")
        )
        print(
            f"{item['end']:>5.1f}s | {result['fusion']['level']:<8} | "
            f"{result['fusion']['score']:>3}/100 | {item['text']}"
        )
    print(json.dumps(service.realtime.close(session_id), ensure_ascii=False))


if __name__ == "__main__":
    main()
