# SCAMTRACE publication-readiness gate

SCAMTRACE is not ready to claim peer-reviewed effectiveness or deployment-grade
accuracy today. It has a reproducible local architecture, a trained language
baseline, deterministic decision contracts, and documented limits. That is a
strong engineering prototype—not yet a validated research result.

## Claim boundary

We may claim:

- local, privacy-preserving prototype operation after model setup;
- layered analysis of conversational manipulation behaviours;
- bounded, explainable attack-path alignment and safety interventions;
- reproducible development checks on the documented data and environment.

We must not claim:

- population scam probability, caller identity, criminality, fraud prevention
  rate, or superiority over platform protections;
- real-call Tamil/Hindi/Hinglish accuracy;
- deepfake detection accuracy from the acoustic anomaly fallback;
- clinical-style safety or production readiness from curated demo cases.

## Evidence required before a research submission

1. **Consented data governance** — obtain naturally recorded, de-identified,
   consented conversations; document retention, access control, annotation
   procedure, language representation, and whether each participant can
   withdraw their data.
2. **Leakage-resistant evaluation** — split by caller/speaker, scam campaign,
   and template family. Keep a hidden test set from a different time period and
   include benign but superficially similar conversations.
3. **Multilingual coverage** — report English, Hindi, Hinglish and Tamil
   independently. Do not let a strong Hinglish template split stand in for every
   target language.
4. **Intervention study** — test whether users understand and can follow the
   Counter-Pressure Protocol under time pressure. Measure comprehension and
   unsafe-action avoidance, never only detector accuracy.
5. **Voice study** — if an anti-spoof model is added, benchmark it on a public
   challenge protocol and a separate telephony-like target set. Report EER,
   min-tDCF or the challenge-relevant metric, calibration and cross-codec
   results. Keep it non-decisive until this gate passes.

## Required metrics

| Layer | Primary measurement | Safety measurement |
| --- | --- | --- |
| ASR | WER/CER by language, code-switch and codec | Error rate on OTP, UPI, bank and authority entities |
| Tactic evidence | Precision/recall by tactic and language | False alerts on safety advice and legitimate banking/courier dialogue |
| Narrative graph | Attack-path recall and false-path rate | Time-to-intervention and correct counterfactual output |
| Fusion | Precision/recall and calibration on held-out data | False alerts per hour or per conversation, reported by cohort |
| Intervention | Comprehension and completion rate | Unsafe action prevented in a consented study; never inferred from score alone |
| Voice authentication | Challenge-aligned anti-spoof metric | Cross-codec / unseen-generator degradation and abstention rate |

## Red-team protocol

The evaluation must include paraphrase, code-switching, dialectal terms,
telephony compression, ASR misspellings, quoted safety advice, two-speaker role
confusion, benign urgency, legitimate bank recovery flows, and attackers who
avoid explicit words such as “OTP” or “transfer.” Each failure becomes a versioned
decision contract only after it is independently reviewed; test-case growth must
not silently become benchmark leakage.

## Promotion criteria

We should promote a component from demo to deployment candidate only if it has
an immutable dataset version, reproducible training recipe, speaker/campaign
disjoint holdout results, language-specific results, calibrated uncertainty,
privacy review, operational rollback, and an approved misuse analysis. A model
that fails any one of those gates may still remain useful in shadow mode.
