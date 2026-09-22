# Security Hardening Review: SCAMTRACE decision layer

## Evidence Basis

We reviewed the local decision pipeline, its model and evaluation documentation,
and its threat model. The inventory and source-hash identity are in
[context.md](context.md). I also compared the direction against Google's public
on-device Scam Detection announcement and the ASVspoof evaluation programme.
That comparison matters: generic on-device call classification is already an
incumbent feature, while voice anti-spoofing remains a generalisation problem.

## Constraints

We must preserve local processing, bounded memory, plain-language explanations
and the deliberate rule that SCAMTRACE neither accuses a caller nor turns a
voice score into a verdict. Current results are development evidence, not field
performance. The next version should become more defensible, not merely more
confident.

## Opportunity Portfolio

| Opportunity | Evidence | Options | Recommendation | Proposal |
| --- | --- | --- | --- | --- |
| Evidence ledger and counter-pressure intervention | Current score ownership, lexical limits, limited evaluation, incumbent Android detection | 1. Local guards; 2. Threat Narrative Graph + Counter-Pressure Protocol; 3. On-device foundation model | Option 2 under current constraints; keep Option 3 in research/shadow mode. | [Complete proposal](proposals/evidence-ledger-intervention.md) |

## Recommendation Summary

The promising idea already exists in the product: an attack is a sequence of
authority, pressure, isolation and extraction, not a deepfake label. What gives
me pause is that the implementation still collapses this insight into a score
and generic advice. We should promote the sequence to a first-class **Threat
Narrative Graph**, then let one **Counter-Pressure Protocol** select the safest
way to break the coercion.

This lets a judge and a user see what is happening, which timestamped evidence
caused concern, what the attacker may seek next, and how to verify safely
without trusting a number supplied by the caller. The response also says what
could reduce concern, such as independent confirmation from an official channel.

Option 1 is necessary tactical protection because phrase coverage and negation
handling still matter. Option 3 may be valuable research, but we should not put
an unvalidated model between a pressured user and an alert. I recommend Option
2 because it creates a testable product moat without weakening privacy, latency
or human accountability.

## Next Decisions

The user requested an industry-grade upgrade, so the recommended structural
option will be implemented as an additive local-only change. A publication-ready
claim remains gated on consented, independent multilingual real-call evaluation
and a validated anti-spoofing benchmark; this design does not pretend those
gates have been passed.
