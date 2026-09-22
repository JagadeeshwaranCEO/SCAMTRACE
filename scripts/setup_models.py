#!/usr/bin/env python3
"""Preflight and optional model download for local-only SCAMTRACE ASR."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import ROOT
from backend.service import ScamTraceService


MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"


def download_model(target: Path) -> None:
    temporary = target.with_suffix(".bin.part")
    print(f"Downloading official whisper.cpp multilingual base model to {target}...")
    try:
        with urllib.request.urlopen(MODEL_URL, timeout=30) as response, temporary.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare SCAMTRACE local ASR.")
    parser.add_argument("--download", action="store_true", help="Download the official multilingual Whisper base model.")
    args = parser.parse_args()
    service = ScamTraceService()
    status = service.asr.status()
    print("SCAMTRACE model preflight")
    print(f"- whisper.cpp binary: {status['binary']}")
    print(f"- model path: {status['model']}")
    if not shutil.which("whisper-cli"):
        print("- missing: whisper.cpp CLI. On macOS run: brew install whisper-cpp", file=sys.stderr)
        raise SystemExit(2)
    target = ROOT / "models" / "ggml-base.bin"
    if not target.exists() and args.download:
        download_model(target)
    elif not target.exists():
        print("- missing model. Run: ./scripts/setup_models.py --download", file=sys.stderr)
        raise SystemExit(2)
    print("- ready: local English, Tamil, Hindi, and Hinglish-capable Whisper base model is installed.")
    print("- inference network dependency: NONE")


if __name__ == "__main__":
    main()

