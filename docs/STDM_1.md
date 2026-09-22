# STDM-1 — SCAMTRACE Threat Decision Model

STDM-1 is a bounded local classifier that estimates the current conversational
attack state:

- NORMAL
- SUSPICIOUS
- IMPERSONATION
- MANIPULATION
- CREDENTIAL_EXTRACTION
- FINANCIAL_EXTRACTION

It consumes a local feature vector containing transcript words and phrases,
language, tactic detections, progression momentum, progression state, and the
existing language-baseline signal. It returns a state distribution, confidence,
and uncertainty. It does not generate prose, identify callers, or make legal
findings.

## Current deployment gate

STDM-1 is in SHADOW_ONLY mode. Its output is visible in the analysis response
but never changes the alert level, recommendation, or evidence-fusion score.
The established evidence-fusion engine remains the intervention authority.

This gate is intentional. The current artifact was trained on 144 reproducible,
authored synthetic hard-negative and attack templates. It is useful for
pipeline development, contrast testing, and measuring calibration mechanics,
but it is not sufficient evidence for real-world deployment.

## Measured model-development result

The latest deterministic family-group development check reports:

- State accuracy: 66.67%
- Macro F1: 66.11%
- Multiclass Brier score: 0.43290
- Expected Calibration Error: 0.30220

These are not deployment metrics. In particular, the ECE is too high for
operational confidence, which is why shadow mode is enforced.

## Reproduce

    .venv/bin/python scripts/generate_stdm_dataset.py
    .venv/bin/python scripts/train_stdm.py

The training process writes the safe JSON artifact to models/stdm_1.json and
the development report to reports/stdm_training.json and
reports/stdm_training.md.

## Promotion criteria

STDM-1 must remain in shadow mode until it has:

1. consented, naturally recorded, multilingual conversation data;
2. speaker-disjoint and template-disjoint train, calibration, and test splits;
3. human-reviewed state and tactic labels;
4. separately reported calibration metrics and false-alert rates by language;
5. a documented decision on the acceptable uncertainty and intervention
   thresholds.

Only then can it be considered as a bounded input to evidence fusion. It must
never become the sole decision-maker.
