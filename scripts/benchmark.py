#!/usr/bin/env python3
"""Measure local model-load and text-analysis performance without network use."""

from __future__ import annotations

import json
import argparse
import resource
import statistics
import sys
import time
import math
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from backend.config import ROOT
from backend.service import ScamTraceService


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark local SCAMTRACE components.")
    parser.add_argument("--audio", type=Path, help="Optional local WAV/MP3/etc. for real ASR timing.")
    parser.add_argument("--asr-runs", type=int, default=3, help="ASR repetitions when --audio is supplied.")
    args = parser.parse_args()
    sample = (
        "This is the cybercrime department. Your Aadhaar is linked to a criminal case. "
        "Do not disconnect. Transfer money to the safe account immediately."
    )
    start = time.perf_counter()
    service = ScamTraceService()
    load_ms = (time.perf_counter() - start) * 1000
    times = []
    cpu_started = time.process_time()
    for _ in range(30):
        started = time.perf_counter()
        service.analyze_text(sample, "en")
        times.append((time.perf_counter() - started) * 1000)
    cpu_per_analysis_ms = (time.process_time() - cpu_started) * 1000 / len(times)
    model_path = ROOT / "models" / "scam_classifier.json"
    asr_measurement = {"measured": False, "reason": "Pass --audio /path/to/clip.wav to measure local ASR latency."}
    if args.audio:
        if not args.audio.is_file():
            raise SystemExit(f"Audio sample not found: {args.audio}")
        asr_times = []
        for _ in range(max(1, args.asr_runs)):
            started = time.perf_counter()
            service.asr.transcribe(args.audio, "en")
            asr_times.append((time.perf_counter() - started) * 1000)
        asr_measurement = {
            "measured": True,
            "sample": args.audio.name,
            "runs": len(asr_times),
            "mean_ms": round(statistics.mean(asr_times), 2),
            "p50_ms": round(statistics.median(asr_times), 2),
            "p95_ms": round(sorted(asr_times)[math.ceil(len(asr_times) * .95) - 1], 2),
        }
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes, Linux reports KiB.
    rss_mb = rss / (1024 * 1024) if __import__("platform").system() == "Darwin" else rss / 1024
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": {"python": __import__("sys").version.split()[0], "platform": __import__("platform").platform()},
        "model_load_ms": round(load_ms, 2),
        "text_analysis_ms": {"runs": len(times), "mean": round(statistics.mean(times), 3), "p50": round(statistics.median(times), 3), "p95": round(sorted(times)[math.ceil(len(times) * .95) - 1], 3)},
        "python_cpu_time_per_text_analysis_ms": round(cpu_per_analysis_ms, 3),
        "peak_rss_mb": round(rss_mb, 2),
        "language_model_size_bytes": model_path.stat().st_size if model_path.exists() else 0,
        "asr_model_size_bytes": service.asr.model_path.stat().st_size if service.asr.model_path.exists() else 0,
        "asr_latency": asr_measurement,
        "asr": service.asr.status(),
        "network_dependency_at_inference": "NONE",
        "note": "ASR latency is reported only once a local whisper.cpp model is installed; this benchmark never makes network calls.",
    }
    (ROOT / "reports" / "performance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = [
        "# SCAMTRACE Performance", "", f"Generated: {report['generated_at']}", "",
        f"- Model load: {report['model_load_ms']} ms",
        f"- Text-analysis mean / p50 / p95: {report['text_analysis_ms']['mean']} / {report['text_analysis_ms']['p50']} / {report['text_analysis_ms']['p95']} ms",
        f"- Python CPU time per text analysis: {report['python_cpu_time_per_text_analysis_ms']} ms",
        f"- Peak process RSS: {report['peak_rss_mb']} MB",
        f"- Language model artifact: {report['language_model_size_bytes']} bytes",
        f"- ASR availability: {report['asr']['available']}",
        f"- ASR model artifact: {report['asr_model_size_bytes']} bytes",
        f"- ASR timing: {report['asr_latency']}",
        "- Network dependency during inference: NONE",
        "", "Peak RSS describes the Python service process; whisper.cpp runs as a separate local process."
    ]
    (ROOT / "reports" / "performance.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
