# SCAMTRACE Regression Evaluation

Generated: 2026-09-25T07:29:39.227451+00:00

## Scope

This is a small hand-curated regression suite used to exercise tactic coverage. It is not an independent held-out evaluation or representative real-world benchmark.

## Results

| System | Accuracy | Precision | Recall | F1 | FPR | FNR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| rule engine only | 100.00% | 100.00% | 100.00% | 100.00% | 0.00% | 0.00% |
| classifier only | 65.00% | 80.00% | 40.00% | 53.33% | 10.00% | 60.00% |
| attack engine only | 85.00% | 100.00% | 70.00% | 82.35% | 0.00% | 30.00% |
| classifier plus attack engine | 85.00% | 88.89% | 80.00% | 84.21% | 10.00% | 20.00% |
| full scamtrace | 100.00% | 100.00% | 100.00% | 100.00% | 0.00% | 0.00% |
| full plus voice signal | 100.00% | 100.00% | 100.00% | 100.00% | 0.00% | 0.00% |

## Voice ablation

No external voice dataset has been incorporated yet, so Full + Voice is intentionally identical to Full. No voice metric is claimed.

## Confusion matrix

- rule_engine_only: TP 10, TN 10, FP 0, FN 0
- classifier_only: TP 4, TN 9, FP 1, FN 6
- attack_engine_only: TP 7, TN 10, FP 0, FN 3
- classifier_plus_attack_engine: TP 8, TN 9, FP 1, FN 2
- full_scamtrace: TP 10, TN 10, FP 0, FN 0
- full_plus_voice_signal: TP 10, TN 10, FP 0, FN 0
