# SCAMTRACE hardening evidence context

This is a derived design-review context, not a security scan or proof that a
proposal is implemented. The source snapshot was inventoried on 2026-09-22.
There is no accessible Git revision in this workspace, so source drift is
unknown.

## Evidence inventory

| ID | Evidence | Path / source | What it establishes |
| --- | --- | --- | --- |
| E01 | Current decision ownership | `backend/service.py`, `backend/attack_engine/progression.py`, `backend/fusion/evidence.py` | The engine returns tactics, progression and a score but has no first-class attack narrative or decision-reversal criterion. |
| E02 | Lexical boundary | `backend/classifiers/taxonomy.py`, `backend/utils/transcript.py` | Direct evidence is auditable but needs explicit polarity control for safety advice and paraphrase resilience. |
| E03 | Realtime boundary | `backend/realtime/session.py`, `docs/THREAT_MODEL.md` | Sessions are bounded and ephemeral, but the response is a score rather than a safety protocol. |
| E04 | Evaluation limits | `docs/MODEL_CARD.md`, `docs/LIMITATIONS.md`, `reports/evaluation.json`, `reports/training_evaluation.json` | Existing results are development checks, not real-call field performance or deepfake accuracy. |
| E05 | Incumbent benchmark | [Google Android Scam Detection](https://blog.google/security/new-ai-powered-scam-detection-features/) | Generic on-device call-scam classification is already an incumbent feature. |
| E06 | Voice generalisation benchmark | [ASVspoof 5 evaluation plan](https://www.asvspoof.org/file/ASVspoof5___Evaluation_Plan_Phase2.pdf) | Anti-spoofing must generalise to unseen adversarial speech, so the acoustic fallback cannot decide risk. |

## Integrity identity

SHA-256 of the sorted per-file SHA-256 inventory for E01–E04:

`04ccf2b44636b8bbbbae90eb723f6b2012696ba93c053658df55ff6c8c9409c5`

This is an ordinary source-and-document collection, not a sealed scan artifact.
