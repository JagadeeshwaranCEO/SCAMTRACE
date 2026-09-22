# Threat Narrative Graph schema

SCAMTRACE emits `scamtrace.threat-narrative-graph/1.0` with every analysis.
The graph is a local, bounded behavioural case record—not a claim about a
person, caller identity, or criminal intent.

## Why this exists

A score alone cannot be audited or safely handed to another system. The graph
preserves how an alert formed:

```text
timestamped evidence --SUPPORTS--> tactic --ALIGNS_WITH--> bounded playbook
```

The detector and fusion engine remain separate. The graph explains a coherent
manipulation chain; fusion owns the non-probabilistic Threat Score; the
Counter-Pressure Protocol owns the recommended safe action.

## Contract

`narrative.graph` contains only these node types:

| Node type | Required fields | Meaning |
| --- | --- | --- |
| `evidence` | `id`, `source`, `source_timestamp_seconds`, `segment_index`, `tactic`, `stage`, `confidence`, `detection_method`, `evidence_phrase` | A timestamped local tactic match. It never includes a full transcript or caller identifier. |
| `tactic` | `id`, `label`, `taxonomy_version` | A normalised social-engineering behaviour. |
| `playbook` | `id`, `label`, `maturity`, `alignment_score`, `alignment_label` | One bounded behavioural pattern, such as digital arrest. Alignment is explicitly not probability. |

Edges have stable IDs and a timestamped `confidence` field:

| Edge | Direction | Meaning |
| --- | --- | --- |
| `SUPPORTS` | evidence → tactic | A local match supports a specific tactic. |
| `ALIGNS_WITH` | tactic → playbook | One or more matched evidence events align a tactic with a bounded playbook. `evidence_ids` makes that provenance inspectable. |

The top-level narrative carries the schema identifier and tactic-taxonomy
version. Consumers must reject or conservatively ignore unknown major schema
versions rather than silently reinterpret an alert.

## Privacy and integration boundary

The runtime graph stays in memory for the active request or bounded realtime
session. It contains no raw audio, full transcript, phone number, caller
identity, contact book, location, device ID, or external account identifier.
The incident export is separately redacted by default.

An authorised bank, cybercrime, or research integration would need a distinct
data-sharing agreement and a versioned adapter. SCAMTRACE does not submit this
graph to any third party, trigger a freeze, or make a report automatically.
