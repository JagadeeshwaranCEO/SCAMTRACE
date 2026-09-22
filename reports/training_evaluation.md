# SCAMTRACE Training Evaluation

Generated: 2026-09-22T17:26:31.317274+00:00

## Data

- Source: ysangam/Indian_Cyber_Scam_PhoneCall_Hinglish_Dataset (Apache-2.0)
- Raw rows: 10000; unique normalized texts: 783; duplicates removed: 9257.
- Input columns: text and label only; category and caller metadata are deliberately excluded to avoid leakage.
- ASR-noise variants: 70; generated from training data only.
- Template families: 538; mixed-label families: 0.

## Template-family validation

Greeting, filler, number and handle variants are grouped before the split. This is intentionally harder than exact-string grouping.

## Candidate comparison

| Candidate | Accuracy | Macro F1 | Balanced accuracy | Balanced Brier | ECE | FPR | FNR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| mnb | 98.71% | 97.25% | 99.26% | 0.0109 | 0.0122 | 0.00% | 1.48% |
| logreg | 98.71% | 97.25% | 99.26% | 0.0074 | 0.0143 | 0.00% | 1.48% |

Selected algorithm: **logreg**.

- Accuracy: 98.71%
- Precision: 100.00%
- Recall: 98.52%
- Scam F1 / macro F1: 99.25% / 97.25%
- Balanced accuracy: 99.26%
- False-positive / false-negative rate: 0.00% / 1.48%
- Balanced Brier / ECE: 0.0074 / 0.0143
- Confusion matrix: {'tp': 133, 'tn': 20, 'fp': 0, 'fn': 2}

## Limits

- Template-family holdout only, not real-world phone-call accuracy.
- The public corpus is Hinglish-focused; Tamil and Hindi need their own labelled validation.
