# Model Card

## SCAMTRACE Multilingual Language Baseline

- Source: the Apache-2.0 licensed [Indian Cyber Scam PhoneCall Hinglish Dataset](https://huggingface.co/datasets/ysangam/Indian_Cyber_Scam_PhoneCall_Hinglish_Dataset), combined with a 40-row team-curated multilingual seed corpus. Training uses text and label only; source metadata is excluded to prevent target leakage.
- Data audit: the 10,040 source rows collapse to 783 unique normalized transcripts after deduplication (9,257 repeats removed). This exposes a strongly template-heavy corpus; it is not treated as 10,040 independent calls. The deduplicated set has 653 scam and 130 benign transcripts across 538 normalized template families.
- Training volume: 628 original transcripts form the training fold; 70 deterministic ASR spelling/spacing variants are generated from that training fold only, yielding 698 fitting records. The template-family validation fold contains 155 original transcripts.
- Split integrity: greeting, filler, number, and handle variants are grouped into a template family before splitting. No augmentation is allowed in validation.
- ASR resilience: training-only variants cover high-value security entities and confusions such as `o t p`, `u p i`, `any desk`, and `aadhar`.
- Algorithm: class-balanced sparse logistic regression over normalized word, phrase, and character n-gram features, with held-out class-balanced calibration. Multinomial Naive Bayes remains a measured candidate baseline, not the selected artifact.
- Artifact: models/scam_classifier.json; safe, inspectable JSON—not pickle.
- Intended purpose: one bounded language signal in a layered, explainable risk engine.
- Not intended for: legal accusation, caller identity, probability claims, or standalone fraud adjudication.
- Evaluation: on the harder template-family holdout, the selected baseline recorded 98.71% accuracy, 97.25% macro F1, 99.26% balanced accuracy, 0.00% FPR, 1.48% FNR, 0.0074 balanced Brier score, and 0.0143 ECE (155 records; TP 133, TN 20, FP 0, FN 2). It was selected over the Naive Bayes candidate because its balanced Brier score was lower (0.0074 vs 0.0109); classification metrics were tied. A separate 20-row curated multilingual regression set passes 20/20 and the internally authored 22-row adversarial decision suite reports TP 14, TN 8, FP 0, FN 0. Neither result is independent or representative of field data.
- Risks: repeated-template corpus structure, phrasing / domain shift, dialect coverage, short-text uncertainty, and lexical correlation.

## STDM-1 — SCAMTRACE Threat Decision Model

- Source: 144 reproducible, authored synthetic hard-negative and attack-template records in data/processed/stdm_synthetic_contrasts.jsonl.
- Algorithm: calibrated multiclass Multinomial Naive Bayes over local transcript, tactic, progression, and language-baseline features.
- Output: a six-state attack distribution and uncertainty value. It is not a caller identity, criminality verdict, or scam probability.
- Deployment: SHADOW_ONLY. The model cannot alter SCAMTRACE alerts or recommendations.
- Development check: family-group split recorded 66.67% state accuracy, 66.11% macro F1, 0.43290 multiclass Brier score, and 0.30220 ECE.
- Critical limitation: authored synthetic development data does not establish real-call performance or field calibration. The measured ECE is not suitable for operational confidence.

## whisper.cpp + ggml-base.bin

- Source: [whisper.cpp](https://github.com/ggml-org/whisper.cpp) and its official multilingual base conversion.
- License: whisper.cpp is MIT; verify applicable upstream model terms before redistribution.
- Intended purpose: local speech-to-text with timestamped segments.
- Evaluation conditions: one official Whisper sample exercised end-to-end in this build; target-language field WER not measured.
- Risks: noisy calls, telephony compression, Tamil/Hindi code-switching, accents, and short speech can degrade transcription.

## Acoustic anomaly fallback

- Source: SCAMTRACE implementation in backend/voice_auth/acoustic.py.
- Inputs: 16-bit WAV amplitude, dynamic range, zero-crossing rate, spectral flatness, and clipping ratio.
- Output: uncertain with an anomaly score; never asserted as a deepfake conclusion.
- Intended purpose: graceful local signal while a licensed, validated ASV/RawTFNet adapter is not installed.
- Key limitation: it is not benchmarked as a synthetic-speech detector and must not be marketed as one.

## Threat Narrative Graph + Counter-Pressure Protocol

- Source: `backend/attack_engine/narrative.py` and `backend/intervention/protocol.py`.
- Algorithm: bounded deterministic alignment across timestamped tactic evidence for digital-arrest, bank-account takeover, courier/customs extortion, family-emergency payment coercion, and remote-device takeover patterns.
- Output: a versioned evidence → tactic → playbook graph, attack-path alignment, observed event provenance, a safe independent-verification action, and a counterfactual condition that could reduce concern.
- Intended purpose: an explainable intervention policy. It is not a learned model, caller-identity system, probability estimator, or legal conclusion.
- Evaluation: unit and demo scenario contracts validate expected chains and safe synthetic speech behavior. This is not independent field evaluation.
- Risks: playbooks can miss novel scam scripts, language variants, speaker roles, subtle deception, or ASR errors. The protocol does not auto-report or contact anyone. Incident exports are redacted by default but a user-selected unredacted local file must still be protected by that user.
