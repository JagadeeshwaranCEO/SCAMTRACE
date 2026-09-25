# SCAMTRACE Performance

Generated: 2026-09-25T07:29:39.273317+00:00

- Model load: 2.78 ms
- Text-analysis mean / p50 / p95: 2.105 / 1.843 / 3.338 ms
- Python CPU time per text analysis: 2.071 ms
- Peak process RSS: 33.38 MB
- Language model artifact: 178548 bytes
- ASR availability: True
- ASR model artifact: 147951465 bytes
- ASR timing: {'measured': False, 'reason': 'Pass --audio /path/to/clip.wav to measure local ASR latency.'}
- Network dependency during inference: NONE

Peak RSS describes the Python service process; whisper.cpp runs as a separate local process.
