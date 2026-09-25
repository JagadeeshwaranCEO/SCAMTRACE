# SCAMTRACE Training Evaluation

Generated: 2026-09-25T07:23:25.452923+00:00

## Data

- Source: ysangam/Indian_Cyber_Scam_PhoneCall_Hinglish_Dataset (Apache-2.0)
- Raw rows: 10000; unique normalized texts: 843; duplicates removed: 9257.
- Input columns: text and label only; category and caller metadata are deliberately excluded to avoid leakage.
- ASR-noise variants: 69; generated from training data only.
- Template families: 598; mixed-label families: 0.

## Template-family validation

Greeting, filler, number and handle variants are grouped before the split. This is intentionally harder than exact-string grouping.

## Candidate comparison

| Candidate | Accuracy | Macro F1 | Balanced accuracy | Balanced Brier | ECE | FPR | FNR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| mnb | 96.51% | 94.50% | 97.87% | 0.0299 | 0.0385 | 0.00% | 4.26% |
| logreg | 97.09% | 95.14% | 95.71% | 0.0625 | 0.1581 | 6.45% | 2.13% |

Selected algorithm: **logreg**.

- Accuracy: 97.09%
- Precision: 98.57%
- Recall: 97.87%
- Scam F1 / macro F1: 98.22% / 95.14%
- Balanced accuracy: 95.71%
- False-positive / false-negative rate: 6.45% / 2.13%
- Balanced Brier / ECE: 0.0625 / 0.1581
- Confusion matrix: {'tp': 138, 'tn': 29, 'fp': 2, 'fn': 3}

## Validation by detected language

| Language | N | Accuracy | Macro F1 | FPR | FNR |
| --- | ---: | ---: | ---: | ---: | ---: |
| en | 121 | 99.17% | 98.59% | 0.00% | 1.00% |
| hi | 5 | 60.00% | 58.33% | 0.00% | 50.00% |
| hinglish | 40 | 100.00% | 100.00% | 0.00% | 0.00% |
| ta | 6 | 66.67% | 66.67% | 50.00% | 0.00% |

## Limits

- Template-family holdout only, not real-world phone-call accuracy.
- The public corpus is Hinglish-focused; Hindi and Tamil additions are authored development data, not an independent real-call benchmark.
