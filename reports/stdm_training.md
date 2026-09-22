# STDM-1 Model Development Report

Generated: 2026-09-21T18:19:08.670973+00:00

## Scope

Synthetic authored contrast development data only. These results are not independent evaluation, real-call accuracy, or a deployment calibration claim.

## Data

- Source: data/processed/stdm_synthetic_contrasts.jsonl
- State distribution: {'NORMAL': 24, 'SUSPICIOUS': 24, 'IMPERSONATION': 24, 'MANIPULATION': 24, 'CREDENTIAL_EXTRACTION': 24, 'FINANCIAL_EXTRACTION': 24}
- Split: deterministic family-group split; template variants remain together

## Results

- State accuracy: 66.67%
- Macro F1: 66.11%
- Multiclass Brier score: 0.43367
- Expected Calibration Error: 0.09708

## Reliability bins

| Bin | N | Mean confidence | Observed accuracy |
| ---: | ---: | ---: | ---: |
| 3 | 8 | 37.04% | 50.00% |
| 4 | 7 | 43.04% | 42.86% |
| 5 | 5 | 57.44% | 40.00% |
| 6 | 2 | 65.58% | 50.00% |
| 7 | 12 | 76.56% | 66.67% |
| 8 | 6 | 85.71% | 100.00% |
| 9 | 8 | 95.23% | 100.00% |
