# ML Hardening Record

## The failure mode we refused to hide

The public Hinglish corpus contains 10,000 rows, but only 783 unique
normalized transcripts after exact deduplication. Treating repeated scripts as
independent examples would make a row-random validation score look stronger
than the model's ability to generalize to a new scam script.

SCAMTRACE therefore does not claim a "10,000-call" model result.

## Hardening decisions

1. **Deduplicate before any split.** The remaining corpus has 653 scam and 130
   benign transcripts; this class imbalance is visible in the reports.
2. **Split by template family.** Greeting, filler, number, and handle changes
   are normalized into one family. The 538 families are partitioned before
   fitting.
3. **Augment only training data.** 70 deterministic ASR spelling variants are
   created after splitting, never in validation.
4. **Compare candidates.** A safe JSON Multinomial Naive Bayes baseline and a
   safe JSON class-balanced sparse logistic baseline are trained on the same
   split.
5. **Choose on score quality, not a flattering threshold metric.** Both models
   reached the same class decision metrics. Logistic regression was selected
   because its balanced Brier score was 0.0074 versus 0.0109 for Naive Bayes.
6. **Keep the model bounded.** The language model is one input to rules,
   progression, narrative alignment, and evidence fusion. It cannot make a
   caller-identity or criminality claim.

## Measured result

On the 155-record template-family holdout, the selected model measured:

- 98.71% accuracy; 97.25% macro F1; 99.26% balanced accuracy
- 0.00% false-positive rate; 1.48% false-negative rate
- 0.0074 balanced Brier score; 0.0143 expected calibration error
- Confusion matrix: TP 133, TN 20, FP 0, FN 2

These are development measurements on a public, template-heavy Hinglish text
corpus. They are not a field false-alert rate, an audio-ASR benchmark, an
independent red-team result, or evidence of Tamil/Hindi parity.

## Promotion gate

No model-only production claim is warranted until SCAMTRACE is evaluated on a
frozen, consented, naturally recorded, speaker-disjoint multilingual corpus.
That study must report calibration, false alerts, missed attacks, and results
by language, channel, and cohort. Until then, the layered decision-support
system remains deliberately conservative and locally operated.

See `reports/training_evaluation.md` for the reproducible candidate comparison
and `docs/DATA_GOVERNANCE.md` for split and privacy constraints.
