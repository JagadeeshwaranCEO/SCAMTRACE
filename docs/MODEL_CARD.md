# Model Card

## SCAMTRACE Multilingual Language Baseline

- Source: the Apache-2.0 licensed [Indian Cyber Scam PhoneCall Hinglish Dataset](https://huggingface.co/datasets/ysangam/Indian_Cyber_Scam_PhoneCall_Hinglish_Dataset), a 40-row team-curated seed corpus, and a balanced 60-row authored Hindi/Tamil development expansion. Training uses transcript text and label only; source metadata is excluded from model features.
- Data audit: the 10,100 input rows collapse to 843 unique normalized transcripts after deduplication (9,257 repeats removed). This exposes a strongly template-heavy public corpus; it is not treated as 10,000 independent calls. The deduplicated set has 683 scam and 160 benign transcripts across 598 normalized template families.
- Training volume: 671 original transcripts form the training fold; 69 deterministic ASR spelling/spacing variants are generated from that training fold only, yielding 740 fitting records. The template-family validation fold contains 172 original transcripts.
- Split integrity: greeting, filler, number, and handle variants are grouped into a template family before splitting. No augmentation is allowed in validation.
- ASR resilience: training-only variants cover high-value security entities and confusions such as `o t p`, `u p i`, `any desk`, and `aadhar`.
- Algorithm: language-and-class-balanced sparse logistic regression over normalized word, phrase, and character n-gram features, with held-out language-and-class-balanced calibration. The selection objective includes worst-language balanced accuracy so the large Hinglish corpus cannot erase smaller native-script strata. Multinomial Naive Bayes remains a measured candidate baseline, not the selected artifact.
- Artifact: models/scam_classifier.json; safe, inspectable JSON—not pickle.
- Intended purpose: one bounded language signal in a layered, explainable risk engine.
- Not intended for: legal accusation, caller identity, probability claims, or standalone fraud adjudication.
- Evaluation: on the template-family holdout, the selected baseline recorded 97.09% accuracy, 95.14% macro F1, 95.71% balanced accuracy, 6.45% FPR, and 2.13% FNR (172 records; TP 138, TN 29, FP 2, FN 3). A separate train-excluded 24-row authored Hindi/Tamil regression set recorded 95.83% classifier accuracy and 100% full-pipeline accuracy (12 scam, 12 benign); the existing 20-row curated multilingual suite also passes 20/20. These are development regression checks—not independent real-call or population-performance estimates.
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
- Evaluation conditions: one official Whisper sample exercised end-to-end in this build; target-language field WER is not measured. Language-specific decoding prompts now preserve common Hindi/Tamil security entities but do not replace acoustic recognition.
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
