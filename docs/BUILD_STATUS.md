# Current Phase

Phase 12 — evidence-ledger, privacy-safe case export, adversarial-resilience verification, and template-leakage-resistant ML validation.

## Completed

- Phase 0 audit: empty non-Git workspace; macOS 26.3.1 arm64; Python 3.14 globally and a project Python 3.11 test environment; Node 22; 113 GiB free disk; ffmpeg and Homebrew available.
- Foundation: local server, configuration, .env parsing, structured local logs, static responsive dashboard, startup checks.
- Text-first engine: auditable English / Tamil / Hindi / Hinglish tactic taxonomy; safe JSON-backed language baseline; sample corpora.
- Model training: Apache-2.0 licensed public Hinglish phone-scam corpus ingested locally. A data audit exposed 10,000 rows collapsing to 783 unique scripts, so training now uses a template-family split, training-only ASR augmentation, class-balanced calibration, and a measured logistic-vs-Naive-Bayes candidate decision.
- Real-time core: bounded local in-memory session manager and REST segment-ingestion interface with expiry, capacity limits, ordered timestamps, explicit close, and no default transcript persistence.
- STDM-1: bounded multiclass threat-state decision model, contrast-data generator, temperature calibration report, Brier/ECE calculation, and a hard SHADOW_ONLY deployment gate.
- Live transcript resilience: codec-aware microphone capture, original-to-normalized security-term correction trail, and grouped ASR-noise language-model augmentation.
- Attack engine: non-linear state history, repeated-evidence accumulation, cross-signal critical escalation, timeline, Scam Momentum.
- Fusion: threat score, LOW / VERIFY / HIGH / CRITICAL levels, explanation, interventions, and uncertainty messaging.
- Threat Narrative Graph: bounded, timestamped alignment for digital-arrest, bank-account takeover, courier/customs, family-emergency, and remote-device takeover coercion patterns.
- Counter-Pressure Protocol: path-specific safe exits, isolation-breaking actions, independent-verification routes, recovery guidance, and counterfactual evidence without auto-reporting.
- Versioned Threat Narrative Graph: a formal `evidence → tactic → playbook` schema with timestamped provenance, stable edge types, tactic-taxonomy version, and no caller-identity or transcript field.
- Privacy-safe case export: incident reports remove `raw_text` and redact likely OTP, PIN/CVV, Aadhaar, PAN, card/account, UPI, email, and phone values by default. An unredacted local export is an explicit UI choice.
- User-controlled incident handoff: the report includes a review checklist and official 1930 / cybercrime.gov.in reference, but never files a report or contacts a bank.
- Local drift and feedback controls: content-free feature-coverage observation and explicit outcome feedback are bounded to process memory, are never telemetry, and cannot alter a live alert or trigger retraining.
- Adversarial decision suite: actual local engine evaluation now covers authored paraphrase, ASR-noise, code-switching, Tamil, Hindi, Hinglish, video-call, remote-access, and tamper-prompt cases.
- Safety-advice polarity guard: quoted advice such as “never share OTP” does not become an active credential-request signal; direct extraction requests still remain visible.
- Derived industry-hardening portfolio: `docs/hardening/` documents current evidence, architecture options, tradeoffs, residual risk, and the selected local-first structural path.
- Audio: whisper.cpp and the local 147 MB multilingual base model installed and exercised end-to-end with an official local ASR test WAV.
- Demo mode: seven deterministic scenarios, including safe human, safe synthetic, human scam, AI scam, Tamil, Hinglish, and remote-access/courier scam.
- Evaluation, performance report, JSON incident report endpoint, and automated tests.

## Working

- ./run.sh launches the local security-layer service on 127.0.0.1:8765; the dashboard is a demo client rather than the product boundary.
- Text / scenario analysis executes fully offline.
- Uploaded WAV, MP3, M4A, AAC, OGG, WebM, and FLAC flow through local temporary storage, local ASR, actual acoustic analysis, and the security engine.
- Browser microphone capture is supported where MediaRecorder permissions are available.
- Core automated tests pass; current artifacts contain the exact measured results.
- scripts/realtime_demo.py proves incremental progression using live engine calls rather than fixture outputs.
- STDM-1 is returned alongside each analysis as a measurable experimental signal and cannot modify alerts.
- The local API and dashboard return a bounded evidence ledger, top playbook alignment, and Counter-Pressure Protocol alongside existing fusion output.
- Dashboard report export visibly defaults to redaction and offers a clear local-only feedback confirmation control.

## Broken

- None in the exercised P0 path.

## Known Limitations

- Live voice authenticity is a transparent acoustic anomaly fallback, not a benchmarked deepfake classifier. It preserves uncertainty rather than making a deceptive claim.
- Tamil/Hindi ASR is supported by the installed base model but has not yet been benchmarked on a labelled regional audio set.
- The public training corpus is Hinglish-focused and template-heavy: 10,000 rows collapse to 783 unique normalized transcripts, including only 130 benign examples after deduplication. Template-family metrics are not a field-performance claim. The separate evaluation set is a small curated regression suite, not an independent field benchmark.
- STDM-1 is trained only on authored synthetic contrast data. Its 0.30220 development ECE is too high for operational confidence, so it remains shadow-only.
- Cellular call interception and Android packaging are deliberately out of scope.
- The Threat Narrative Graph is a transparent bounded policy, not a broad semantic model. It needs independent, consented multilingual real-call evaluation before any publishable effectiveness claim.
- The current adversarial suite is internally authored and was used to improve coverage. Its measured result is useful as a release gate but is not a frozen independent benchmark.
- SCAMTRACE does not yet integrate native Android, WhatsApp, Skype, or ordinary dialer capture. Any future integration must be explicit-consent, platform-policy-compliant, and non-covert.

## Next Actions

- Highest-value next work: acquire consented, speaker-disjoint, naturally recorded multilingual call data and benchmark false alerts, attack-path coverage, intervention usefulness, and calibration by cohort.
- Optional: integrate and benchmark a licensed RawTFNet/ASV checkpoint with a real labelled voice corpus.
- Optional: connect the real-time API to a local Android or desktop ASR client.
- Essential research work: collect consented multilingual conversation data with speaker-disjoint labels before promoting STDM-1.
- Essential evaluation work: freeze a fresh, independently reviewed adversarial set before the next taxonomy or model revision; report errors by language, channel, and user cohort.

## Test Results

- pytest: 32 passed after versioned evidence-graph, redacted-report, feedback, drift, tamper-evasion, real-time, narrative, microphone, transcript-resilience, and robust-training changes.
- Local audio → whisper.cpp → analysis: passed with local model.
- Training template-family check: 98.71% accuracy, 97.25% macro F1, 99.26% balanced accuracy, 0.00% FPR, 1.48% FNR, 0.0074 balanced Brier, and 0.0143 ECE on 155 held-out public-corpus transcripts. The selected class-balanced logistic baseline tied Naive Bayes on classification but improved balanced Brier from 0.0109 to 0.0074; not a deployment benchmark.
- Regression: Full SCAMTRACE 20/20 on the curated multilingual 20-row suite. It verifies current expected behavior and is not an independent evaluation benchmark.
- STDM-1 development: 66.67% state accuracy, 66.11% macro F1, Brier 0.43290, ECE 0.30220 on authored family-group contrast data. Shadow-only by design.
- Performance: text analysis mean 1.319 ms after graph, redaction, tamper-evasion, aggregate-only monitoring, and the robust language artifact; peak RSS 32.91 MB. ASR latency was not rerun in the latest benchmark without an audio argument; the prior local Whisper run measured 1075.45 ms on a 10.5-second local validation clip.
- Behavioural decision contracts: 8/8 deterministic contracts pass for safe advice, safe context, digital arrest, bank takeover, remote takeover, courier, family emergency, and Tamil digital arrest. This is a design-contract suite, not a field benchmark.
- Adversarial decision gate: 22/22 authored cases reached the expected engine decision (8 benign, 14 scam; TP 14, TN 8, FP 0, FN 0; precision/recall/F1 1.0). This is a post-improvement internal robustness gate, not independent or field performance.

## Demo Readiness

READY for a local text/scenario demo, local audio upload demo, and segment-by-segment evidence-ledger demo. Show the Threat Narrative Graph after the score, then export the redacted case report: this demonstrates an auditable intervention system rather than a suspicious-phrase detector. Keep Wi-Fi disabled after local model setup to demonstrate offline operation.
