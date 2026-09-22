# Training Data Governance

## Primary training corpus

The default training command uses the public Apache-2.0 licensed
[Indian Cyber Scam PhoneCall Hinglish Dataset](https://huggingface.co/datasets/ysangam/Indian_Cyber_Scam_PhoneCall_Hinglish_Dataset).

Only the text and binary label columns are used for model fitting. The corpus
metadata columns, including scam category, caller type, urgency, blackmail
flag, and audio duration, are intentionally excluded because those fields
would leak the answer into a text-only classifier.

## Split integrity

Rows are normalized and deduplicated before splitting. The current data audit
found that 10,000 source rows collapse to 783 unique normalized transcripts,
so source-row random splits would create an invalidly easy result. The
deterministic validation split groups a *template family*: greeting, filler,
number, and handle variants of a script stay together. Exact or superficial
template variants therefore cannot occur on both sides of the split.

The language-training command also creates at most one local ASR spelling
variant for a source row when it contains a high-value security term. Examples
include spaced forms such as "o t p", "u p i", "any desk", and "aadhar".
Variants are created only after the template-family split and only for the
training fold, so augmentation cannot leak a source script into validation.

## What the result does and does not mean

The recorded validation result measures performance on the held-out templates
from this corpus. It is not a claim about real-world call prevalence,
adversarial robustness, audio transcription error, or population-level false
positive rates.

The source corpus is Hinglish-focused. English, Tamil, and Hindi rules are
implemented separately, while those languages require independently labelled,
consented validation data before comparative accuracy claims can be made.

The repository's small curated multilingual file is a regression suite. It
checks expected protective behavior while the tactic taxonomy evolves; it must
not be presented as a held-out model benchmark.

## Adversarial decision evaluation

`data/evaluation/adversarial_redteam_v1.jsonl` is an internally authored
red-team decision suite. It includes benign safety guidance plus scam cases
with paraphrase, ASR-noise, code-switching, Tamil, Hindi, Hinglish, remote
access, video-call, and attacker-tamper language. The evaluator reports actual
engine precision, recall, F1, false-positive rate, and false-negative rate.

Because this suite is authored and used to improve the taxonomy, it is a
transparent robustness gate—not a held-out benchmark or field-performance
claim. A release-quality study needs consented, naturally occurring,
speaker-disjoint conversations collected under a reviewed protocol, frozen
before model and rule selection.

## Privacy

Training runs locally from a downloaded CSV and creates a JSON model artifact.
The runtime does not upload call audio or transcripts. Raw user audio is
processed in an ephemeral local directory and is not persisted by default.
