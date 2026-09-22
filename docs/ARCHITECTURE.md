# Architecture

SCAMTRACE is a local decision-support pipeline designed so one weak signal cannot label a caller as a criminal.

    Input
      |- typed transcript / deterministic scenario
      |- incremental local-ASR transcript segments
      |- audio file / browser microphone
             |- file validation, temporary local file
             |- local whisper.cpp ASR -> timestamped segments
             |- acoustic anomaly measurement
                        |
                        v
              phrase & tactic detector + polarity guard
              JSON language baseline
                        |
                        v
           non-linear attack progression
                        |
                        v
          Threat Narrative Graph (bounded playbooks)
                        |
                        v
              evidence fusion / counter-pressure protocol
                        |
                        v
     local security-layer response, dashboard, versioned case graph,
     redacted report export, aggregate-only feedback and drift review

## Components

- backend/asr/local_whisper.py invokes an already-installed whisper.cpp model; it does not download or call a service at inference.
- backend/classifiers/taxonomy.py provides direct phrase evidence with attack categories and mapped stages.
- backend/classifiers/scam_classifier.py provides a reproducible calibrated Multinomial Naive Bayes baseline trained from licensed public data; its artifact is safe JSON rather than pickle.
- backend/realtime/session.py provides bounded in-memory sessions for timestamped transcript segments. Sessions expire and are never persisted.
- backend/attack_engine/progression.py accumulates tactics across timestamped segments, permits branches, and adds repeated/cross-signal evidence.
- backend/attack_engine/narrative.py creates an ordered evidence ledger and a versioned evidence → tactic → playbook graph. Alignment is not a probability, caller identity, or criminal finding.
- backend/fusion/evidence.py produces a capped, interpretable score. Tactic behavior dominates the language baseline; direct credential, payment, and remote-access demands receive an explicit intervention weight.
- backend/intervention/protocol.py selects a threat-aware safe exit, independent-verification message, recovery action, and counterfactual condition. It never contacts a caller, bank, authority, or reporting channel automatically.
- backend/reports/redaction.py applies default credential and identity redaction at the export boundary; `backend/reports/incident.py` creates a user-controlled 1930 / cybercrime.gov.in handoff checklist without external submission.
- backend/observability/ contains content-free local feature-coverage and explicit feedback aggregates. Neither stores a transcript or changes a live decision.
- backend/voice_auth/acoustic.py measures real signals but intentionally returns uncertainty without a validated anti-spoof model.
- backend/main.py provides a local-only HTTP server with JSON body limits, filename sanitization, response headers, and static-file path restrictions.

## Reliability decisions

The server continues if audio voice analysis fails. If local ASR is unavailable, text and demos still work and the UI gives an actionable setup message. GPU was disabled in the whisper adapter after an Apple Metal allocation fault in this environment; CPU mode is slower but reproducible.

## Decision ownership

The Threat Narrative Graph is deliberately separate from fusion. It owns the
question “does this sequence align with a bounded manipulation playbook?” Fusion
still owns the non-probabilistic threat score. The Counter-Pressure Protocol
owns “what is the safest next action?” This avoids accidentally turning a model
or phrase contribution into an unexplained user instruction.
