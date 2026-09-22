#!/usr/bin/env python3
"""Train SCAMTRACE from a local real corpus with group-aware validation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.classifiers.scam_classifier import calibrate_model, predict_model, train_logistic_model, train_model
from backend.config import ROOT
from backend.utils.text import normalize_text


DEFAULT_DATASET = ROOT / "data" / "raw" / "India_Cyber_Scam_Hinglish_Dataset.csv"
SEED_DATASET = ROOT / "data" / "processed" / "training_seed.jsonl"
ASR_VARIANTS = (
    (r"\botp\b", "o t p"),
    (r"\bcvv\b", "c v v"),
    (r"\bupi\b", "u p i"),
    (r"\bkyc\b", "k y c"),
    (r"\baadhaar\b", "aadhar"),
    (r"\banydesk\b", "any desk"),
    (r"\bteamviewer\b", "team viewer"),
    (r"\bcybercrime\b", "cyber crime"),
)

# Dataset greetings, fillers and variable identifiers can create deceptively
# easy train/test splits. We group those superficial variants into a shared
# template family before validation. This is still not a real-call holdout, but
# it is intentionally harder than exact-string grouping.
TEMPLATE_FILLERS = {
    "aap", "aapka", "aapke", "aapko", "aapki", "hello", "ji", "namaste", "sir", "madam", "ma'am",
    "please", "suniye", "suno", "haan", "ek", "minute", "beta",
}


def template_family(text: str) -> str:
    """Create a stable, content-reduced group key for near-template variants."""
    normalized = normalize_text(text)
    normalized = re.sub(r"₹\s*\d+(?:[.,]\d+)?|\b\d+(?:[.,]\d+)?\b", "<num>", normalized)
    normalized = re.sub(r"\b[a-z0-9._-]{2,}@[a-z0-9.-]+\b", "<handle>", normalized)
    words = [word for word in re.findall(r"[\w\u0900-\u097F\u0B80-\u0BFF<>]+", normalized) if word not in TEMPLATE_FILLERS]
    return " ".join(words) or normalized


def assign_template_groups(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    assigned = [{**row, "group_id": template_family(row["text"])} for row in rows]
    groups: dict[str, set[str]] = defaultdict(set)
    for row in assigned:
        groups[row["group_id"]].add(row["label"])
    return assigned, {
        "template_families": len(groups),
        "mixed_label_template_families": sum(len(labels) > 1 for labels in groups.values()),
    }


def load_real_rows(source: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"text", "label"} <= set(reader.fieldnames or []):
            raise ValueError(f"Dataset needs text and label; found {reader.fieldnames}")
        raw_rows = list(reader)
    rows = []
    mapping = {"1": "scam", "0": "benign", "scam": "scam", "benign": "benign"}
    for row in raw_rows:
        label = mapping.get((row.get("label") or "").strip().lower())
        if label and (row.get("text") or "").strip():
            rows.append({"text": row["text"], "label": label, "source": "ysangam"})
    return rows, {
        "name": "ysangam/Indian_Cyber_Scam_PhoneCall_Hinglish_Dataset",
        "license": "Apache-2.0",
        "path": str(source),
        "raw_rows": len(rows),
        "columns_used": ["text", "label"],
    }


def load_seed_rows() -> list[dict[str, str]]:
    return [
        {**json.loads(line), "source": "scamtrace_curated_seed"}
        for line in SEED_DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def deduplicate_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, int]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[normalize_text(row["text"])].append(row)
    clean, conflicts, duplicates = [], 0, 0
    for group in grouped.values():
        labels = {row["label"] for row in group}
        if len(labels) != 1:
            conflicts += 1
            continue
        duplicates += len(group) - 1
        clean.append(group[0])
    return clean, {"unique_rows": len(clean), "duplicates_removed": duplicates, "conflicting_texts_dropped": conflicts}


def group_split(rows: list[dict[str, str]], validation_fraction: float = 0.2) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    by_label: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        group_id = str(row.get("group_id") or normalize_text(row["text"]))
        by_label[row["label"]][group_id].append(row)
    train, validation = [], []
    for groups in by_label.values():
        ordered = sorted(groups.items(), key=lambda item: hashlib.blake2b(item[0].encode(), digest_size=8).hexdigest())
        validation_count = max(1, round(len(ordered) * validation_fraction))
        for _, items in ordered[:validation_count]:
            validation.extend(items)
        for _, items in ordered[validation_count:]:
            train.extend(items)
    return train, validation


def asr_noise_augment(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    """Create one common ASR-spelling variant per matching source row.

    Variants inherit an explicit group_id, so the original and its noisy form
    are always assigned to the same split and cannot leak validation evidence.
    """
    augmented = []
    for row in rows:
        source = str(row["text"])
        group_id = str(row.get("group_id") or normalize_text(source))
        base = {**row, "group_id": group_id}
        augmented.append(base)
        for pattern, replacement in ASR_VARIANTS:
            noisy, count = re.subn(pattern, replacement, source, count=1, flags=re.IGNORECASE)
            if count and noisy != source:
                augmented.append({**base, "text": noisy, "source": "asr_noise_augmentation"})
                break
    return augmented, len(augmented) - len(rows)


def classification_metrics(rows: list[dict[str, str]], model: dict[str, Any]) -> dict[str, Any]:
    matrix = Counter()
    for row in rows:
        predicted = predict_model(model, row["text"])["scam_score"] >= 0.5
        actual = row["label"] == "scam"
        key = "tp" if predicted and actual else "tn" if not predicted and not actual else "fp" if predicted else "fn"
        matrix[key] += 1
    tp, tn, fp, fn = (matrix[name] for name in ("tp", "tn", "fp", "fn"))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    benign_precision = tn / (tn + fn) if tn + fn else 0.0
    benign_recall = tn / (tn + fp) if tn + fp else 0.0
    scam_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    benign_f1 = 2 * benign_precision * benign_recall / (benign_precision + benign_recall) if benign_precision + benign_recall else 0.0
    return {
        "n": len(rows),
        "accuracy": round((tp + tn) / len(rows), 4) if rows else 0.0,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(scam_f1, 4),
        "balanced_accuracy": round((recall + benign_recall) / 2, 4),
        "macro_f1": round((scam_f1 + benign_f1) / 2, 4),
        "false_positive_rate": round(fp / (fp + tn), 4) if fp + tn else None,
        "false_negative_rate": round(fn / (fn + tp), 4) if fn + tp else None,
        "confusion_matrix": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
    }


def probability_metrics(rows: list[dict[str, str]], model: dict[str, Any]) -> dict[str, float]:
    """Measure score quality separately from the alert decision threshold."""
    values = [(predict_model(model, row["text"])["scam_score"], 1 if row["label"] == "scam" else 0) for row in rows]
    by_label: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for value in values:
        by_label[value[1]].append(value)

    def log_loss(items: list[tuple[float, int]]) -> float:
        return sum(
            -(label * math.log(max(score, 1e-8)) + (1 - label) * math.log(max(1 - score, 1e-8)))
            for score, label in items
        ) / max(1, len(items))

    brier = sum((score - label) ** 2 for score, label in values) / max(1, len(values))
    balanced_brier = sum(sum((score - label) ** 2 for score, label in items) / max(1, len(items)) for items in by_label.values()) / 2
    balanced_log_loss = sum(log_loss(items) for items in by_label.values()) / 2
    bins: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for value in values:
        bins[min(9, int(value[0] * 10))].append(value)
    expected_calibration_error = sum(
        len(items) / max(1, len(values)) * abs(sum(score for score, _ in items) / len(items) - sum(label for _, label in items) / len(items))
        for items in bins.values()
    )
    return {
        "brier_score": round(brier, 6),
        "balanced_brier_score": round(balanced_brier, 6),
        "balanced_log_loss": round(balanced_log_loss, 6),
        "expected_calibration_error": round(expected_calibration_error, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--seed-only", action="store_true")
    parser.add_argument("--without-seed", action="store_true")
    parser.add_argument("--without-asr-augmentation", action="store_true")
    parser.add_argument("--algorithm", choices=("auto", "mnb", "logreg"), default="auto")
    args = parser.parse_args()

    if args.seed_only:
        raw_rows, source_metadata = load_seed_rows(), {"name": "SCAMTRACE curated seed", "raw_rows": 40}
    else:
        if not args.dataset.exists():
            raise SystemExit(f"Dataset unavailable: {args.dataset}")
        raw_rows, source_metadata = load_real_rows(args.dataset)
        if not args.without_seed:
            raw_rows.extend(load_seed_rows())
            source_metadata["seed_rows_added"] = 40
    rows, dedupe_metadata = deduplicate_rows(raw_rows)
    rows, family_metadata = assign_template_groups(rows)
    train_rows, validation_rows = group_split(rows)
    asr_variants_added = 0
    train_for_model = train_rows
    if not args.without_asr_augmentation:
        train_for_model, asr_variants_added = asr_noise_augment(train_rows)
        source_metadata["asr_noise_variants_added"] = asr_variants_added
    metadata = {
        "trained_at": datetime.now(UTC).isoformat(),
        "source": source_metadata,
        "deduplication": dedupe_metadata,
        "split": {
            "method": "deterministic template-family group split; augmentation is train-only",
            "validation_fraction": 0.2,
            "train_rows": len(train_rows),
            "validation_rows": len(validation_rows),
        },
    }
    candidates = {
        "mnb": train_model(train_for_model, output_path=None, metadata=metadata, min_feature_count=2),
        "logreg": train_logistic_model(train_for_model, output_path=None, metadata=metadata, min_feature_count=2),
    }
    candidates = {name: calibrate_model(model, validation_rows, class_balanced=True) for name, model in candidates.items()}
    candidate_metrics = {
        name: {**classification_metrics(validation_rows, model), "probability_quality": probability_metrics(validation_rows, model)}
        for name, model in candidates.items()
    }
    if args.algorithm == "auto":
        # We optimise for balanced score quality, then threshold behaviour and
        # finally penalise false alerts. Accuracy alone would hide the corpus
        # template imbalance.
        selected = max(
            candidates,
            key=lambda name: (
                -float(candidate_metrics[name]["probability_quality"]["balanced_brier_score"]),
                candidate_metrics[name]["macro_f1"],
                candidate_metrics[name]["balanced_accuracy"],
                -float(candidate_metrics[name]["false_positive_rate"] or 0.0),
            ),
        )
    else:
        selected = args.algorithm
    model = candidates[selected]
    validation_metrics = candidate_metrics[selected]
    model["metadata"]["validation_metrics"] = validation_metrics
    model["metadata"]["candidate_metrics"] = candidate_metrics
    model["metadata"]["selected_algorithm"] = selected
    model["metadata"]["validation_note"] = "Template-family holdout only, not real-world phone-call accuracy."
    target = ROOT / "models" / "scam_classifier.json"
    target.write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "generated_at": metadata["trained_at"],
        "model": {"name": model["model_name"], "algorithm": model["algorithm"], "feature_count": len(model.get("log_odds") or model.get("weights") or {})},
        "data": {**source_metadata, **dedupe_metadata, **family_metadata, "class_distribution_after_deduplication": dict(Counter(row["label"] for row in rows))},
        "split": metadata["split"],
        "calibration": model["calibration"],
        "validation_metrics": validation_metrics,
        "candidate_metrics": candidate_metrics,
        "selected_algorithm": selected,
        "limitations": [
            model["metadata"]["validation_note"],
            "The public corpus is Hinglish-focused; Tamil and Hindi need their own labelled validation.",
        ],
    }
    (ROOT / "reports" / "training_evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = [
        "# SCAMTRACE Training Evaluation", "", f"Generated: {report['generated_at']}", "",
        "## Data", "", f"- Source: {source_metadata['name']} ({source_metadata.get('license', 'local curated')})",
        f"- Raw rows: {source_metadata['raw_rows']}; unique normalized texts: {dedupe_metadata['unique_rows']}; duplicates removed: {dedupe_metadata['duplicates_removed']}.",
        "- Input columns: text and label only; category and caller metadata are deliberately excluded to avoid leakage.",
        f"- ASR-noise variants: {asr_variants_added}; generated from training data only.",
        f"- Template families: {family_metadata['template_families']}; mixed-label families: {family_metadata['mixed_label_template_families']}.",
        "", "## Template-family validation", "", "Greeting, filler, number and handle variants are grouped before the split. This is intentionally harder than exact-string grouping.", "",
        "## Candidate comparison", "", "| Candidate | Accuracy | Macro F1 | Balanced accuracy | Balanced Brier | ECE | FPR | FNR |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        *[f"| {name} | {value['accuracy']:.2%} | {value['macro_f1']:.2%} | {value['balanced_accuracy']:.2%} | {value['probability_quality']['balanced_brier_score']:.4f} | {value['probability_quality']['expected_calibration_error']:.4f} | {value['false_positive_rate']:.2%} | {value['false_negative_rate']:.2%} |" for name, value in candidate_metrics.items()],
        f"", f"Selected algorithm: **{selected}**.", "",
        f"- Accuracy: {validation_metrics['accuracy']:.2%}",
        f"- Precision: {validation_metrics['precision']:.2%}",
        f"- Recall: {validation_metrics['recall']:.2%}",
        f"- Scam F1 / macro F1: {validation_metrics['f1']:.2%} / {validation_metrics['macro_f1']:.2%}",
        f"- Balanced accuracy: {validation_metrics['balanced_accuracy']:.2%}",
        f"- False-positive / false-negative rate: {validation_metrics['false_positive_rate']:.2%} / {validation_metrics['false_negative_rate']:.2%}",
        f"- Balanced Brier / ECE: {validation_metrics['probability_quality']['balanced_brier_score']:.4f} / {validation_metrics['probability_quality']['expected_calibration_error']:.4f}",
        f"- Confusion matrix: {validation_metrics['confusion_matrix']}",
        "", "## Limits", "",
        *[f"- {item}" for item in report["limitations"]],
    ]
    (ROOT / "reports" / "training_evaluation.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved trained safe JSON model to {target}")


if __name__ == "__main__":
    main()
