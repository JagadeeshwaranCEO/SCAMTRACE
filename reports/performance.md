# SCAMTRACE Performance

Generated: 2026-09-22T17:26:34.834683+00:00

- Model load: 1.45 ms
- Text-analysis mean / p50 / p95: 1.319 / 1.203 / 1.488 ms
- Python CPU time per text analysis: 1.311 ms
- Peak process RSS: 32.91 MB
- Language model artifact: 120330 bytes
- ASR availability: True
- ASR model artifact: 147951465 bytes
- ASR timing: {'measured': False, 'reason': 'Pass --audio /path/to/clip.wav to measure local ASR latency.'}
- Network dependency during inference: NONE

Peak RSS describes the Python service process; whisper.cpp runs as a separate local process.
