# Privacy

SCAMTRACE defaults to local, ephemeral handling.

| Item | Behavior |
| --- | --- |
| Audio processing | Local machine only |
| ASR | Local whisper.cpp binary and local model |
| Language / fusion | Local Python process |
| Cloud APIs | None |
| Raw audio persistence | No; temporary file is removed after analysis |
| Transcript persistence | No; only kept in browser/server memory for the active request |
| Incident report | Downloaded only when the user explicitly exports it; credential/identity values are redacted by default |
| Explicit feedback | Aggregate decision outcome only, held in local process memory and cleared when SCAMTRACE stops |
| Drift monitor | Aggregate feature-coverage ratios only; no transcript, audio, phrases, or identifiers |
| Logs | Structured events without transcript or raw audio |

The one-time model installation download is not inference. Once the model is in models/, the application can demonstrate its core functions with network disabled.

## Export boundary

The active dashboard may display the user's own transcript in memory. Export is
a separate boundary: reports exclude `raw_text` and redact likely OTP, PIN/CVV,
Aadhaar, PAN, card/account, UPI ID, email, and phone values by default. A user
can deliberately choose a local unredacted export, with a visible warning; that
does not send the report anywhere.

Feedback is an explicit confirmation action, not background telemetry. It
records only outcome, language, alert-level, and a score band. It cannot
retrain the model or alter a live alert.
