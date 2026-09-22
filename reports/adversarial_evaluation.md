# SCAMTRACE Adversarial Decision Evaluation v1

Generated: 2026-09-22T17:26:34.629324+00:00

Internally authored red-team cases; 8 benign and 14 scam examples across paraphrase, ASR-noise, code-switching, and regional-language conditions.

Measured local-engine decision outcomes. Not independent field evaluation, population calibration, model-only evaluation, or a claim of real-world prevalence.

## Result: PASS

| Metric | Value |
| --- | ---: |
| confusion matrix | {"tp": 14, "fp": 0, "tn": 8, "fn": 0} |
| precision | 1.0 |
| recall | 1.0 |
| f1 | 1.0 |
| false positive rate | 0.0 |
| false negative rate | 0.0 |

## Case outcomes

| ID | Label | Language | Perturbation | Level | Path | Correct decision |
| --- | --- | --- | --- | --- | --- | --- |
| AR01 | benign | en | protective_guidance | LOW | none | yes |
| AR02 | benign | en | family_context | LOW | none | yes |
| AR03 | benign | hinglish | code_switch_safe | LOW | none | yes |
| AR04 | benign | ta | regional_safety_advice | LOW | none | yes |
| AR05 | benign | en | remote_support_context | LOW | none | yes |
| AR06 | benign | en | courier_context | LOW | none | yes |
| AR07 | benign | hi | public_awareness | LOW | none | yes |
| AR08 | benign | en | bank_routine | LOW | none | yes |
| AR09 | scam | en | paraphrase | CRITICAL | digital_arrest | yes |
| AR10 | scam | en | asr_noise | CRITICAL | bank_account_takeover | yes |
| AR11 | scam | en | remote_access_paraphrase | CRITICAL | remote_device_takeover | yes |
| AR12 | scam | en | courier_paraphrase | CRITICAL | courier_customs_extortion | yes |
| AR13 | scam | en | family_emotion | CRITICAL | family_emergency_payment | yes |
| AR14 | scam | hinglish | code_switch | CRITICAL | bank_account_takeover | yes |
| AR15 | scam | hi | hindi_script | CRITICAL | digital_arrest | yes |
| AR16 | scam | ta | tamil_script | CRITICAL | digital_arrest | yes |
| AR17 | scam | en | credential_synonym | CRITICAL | bank_account_takeover | yes |
| AR18 | scam | en | payment_euphemism | CRITICAL | none | yes |
| AR19 | scam | hinglish | spelling_variant | CRITICAL | remote_device_takeover | yes |
| AR20 | scam | en | attacker_tamper_prompt | CRITICAL | digital_arrest | yes |
| AR21 | scam | en | minimal_direct_action | CRITICAL | bank_account_takeover | yes |
| AR22 | scam | hi | code_switch_asr_noise | CRITICAL | courier_customs_extortion | yes |
