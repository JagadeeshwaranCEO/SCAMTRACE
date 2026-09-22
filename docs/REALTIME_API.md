# Real-time Security-Layer API

SCAMTRACE exposes a local, process-memory interface for an on-device speech
recognizer or conversation client. It is not a cloud API and does not persist
raw audio or transcript text.

## Start a session

Send a JSON request to POST /api/realtime/session.

    {"language":"en"}

The response contains an opaque 32-character session identifier. Sessions are
local to the running process, limited to 32 by default, and expire after 900
seconds of inactivity.

## Submit ASR segments

Send each finalized local-ASR segment to POST
/api/realtime/session/{session_id}/segment.

    {"text":"This is the bank security team. Do not disconnect.","start":0,"end":4,"language":"en"}

The result is a complete current decision, including the current score,
threat level, evidence, state history, and a realtime field. The realtime
alert field becomes true for HIGH and CRITICAL levels.

Timestamps must be non-negative. Out-of-order timestamps are safely clamped
to preserve an ordered local timeline. A session accepts at most 500 segments.

## Inspect or close

GET /api/realtime/session/{session_id} returns metadata only, never the
transcript. POST /api/realtime/session/{session_id}/close erases the
in-memory segment buffer immediately.

## Local proof

Run:

    .venv/bin/python scripts/realtime_demo.py --scenario human_digital_arrest

The expected progression is VERIFY, HIGH, HIGH, then CRITICAL as evidence
accumulates. This is the intended integration point for streaming ASR; the
dashboard is optional.
