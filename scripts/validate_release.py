#!/usr/bin/env python3
"""Validate the checked-in, offline-safe release artifacts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    model_path = ROOT / "models" / "scam_classifier.json"
    if not model_path.is_file():
        raise SystemExit("Missing checked-in language model artifact.")
    model = json.loads(model_path.read_text(encoding="utf-8"))
    required = {"format", "model_name", "version", "feature_config", "weights", "calibration"}
    missing = required - set(model)
    if missing:
        raise SystemExit(f"Model artifact is missing fields: {sorted(missing)}")
    if model["format"] not in {"scamtrace-logreg-v1", "scamtrace-mnb-v2"}:
        raise SystemExit(f"Unsupported unsafe model format: {model['format']}")
    if not isinstance(model["weights"], dict) or not model["weights"]:
        raise SystemExit("Model weights are empty or malformed.")
    forbidden = {"pickle", "cloud_api", "openai", "anthropic"}
    artifact_text = model_path.read_text(encoding="utf-8").lower()
    if any(term in artifact_text for term in forbidden):
        raise SystemExit("Model artifact contains a forbidden runtime dependency marker.")
    print(json.dumps({
        "status": "pass",
        "format": model["format"],
        "version": model["version"],
        "features": len(model["weights"]),
        "network_dependency": "NONE",
    }, indent=2))


if __name__ == "__main__":
    main()
