from backend.classifiers.scam_classifier import calibrate_model, predict_model, train_logistic_model, train_model
from scripts.train_scam_classifier import asr_noise_augment, deduplicate_rows, group_split, template_family


def test_group_deduplication_keeps_duplicate_scripts_together() -> None:
    rows = [
        {"text": "Aapka account block hoga", "label": "scam"},
        {"text": "Aapka account block hoga ", "label": "scam"},
        {"text": "Kal coffee pe milte hain", "label": "benign"},
        {"text": "Ghar aa gaya hoon", "label": "benign"},
        {"text": "OTP batao abhi", "label": "scam"},
        {"text": "Meeting kal hai", "label": "benign"},
    ]
    unique, metadata = deduplicate_rows(rows)
    train, validation = group_split(unique, validation_fraction=0.4)
    assert metadata["duplicates_removed"] == 1
    assert {row["text"].strip() for row in train}.isdisjoint({row["text"].strip() for row in validation})


def test_v2_model_uses_character_evidence_and_calibration(tmp_path) -> None:
    train = [
        {"text": "OTP batao abhi account block hoga", "label": "scam"},
        {"text": "transfer money safe account now", "label": "scam"},
        {"text": "kal coffee pe milte hain", "label": "benign"},
        {"text": "cab paanch minute mein pahunch raha hai", "label": "benign"},
    ]
    model = train_model(train, output_path=tmp_path / "model.json", feature_config={"char_ngrams": True, "char_min": 3, "char_max": 3})
    calibrated = calibrate_model(model, train)
    assert calibrated["format"] == "scamtrace-mnb-v2"
    assert calibrated["calibration"]["method"].startswith("grid-search")
    assert predict_model(calibrated, "OTP batao abhi")["scam_score"] > 0.5


def test_asr_spelling_variants_stay_with_their_source_group() -> None:
    augmented, count = asr_noise_augment([
        {"text": "Tell me the OTP now", "label": "scam"},
        {"text": "Never share OTP with strangers", "label": "benign"},
        {"text": "Meeting tomorrow", "label": "benign"},
        {"text": "Transfer money now", "label": "scam"},
    ])
    assert count == 2
    train, validation = group_split(augmented, validation_fraction=0.5)
    train_groups = {row["group_id"] for row in train}
    validation_groups = {row["group_id"] for row in validation}
    assert train_groups.isdisjoint(validation_groups)


def test_robust_logistic_baseline_is_safe_json_and_balances_classes(tmp_path) -> None:
    train = [
        {"text": "OTP batao abhi account block hoga", "label": "scam"},
        {"text": "transfer money safe account now", "label": "scam"},
        {"text": "cyber cell se call hai OTP do", "label": "scam"},
        {"text": "kal coffee pe milte hain", "label": "benign"},
        {"text": "cab paanch minute mein pahunch raha hai", "label": "benign"},
    ]
    model = train_logistic_model(train, output_path=tmp_path / "model.json", feature_config={"char_ngrams": False}, epochs=30)
    calibrated = calibrate_model(model, train, class_balanced=True)
    assert calibrated["format"] == "scamtrace-logreg-v1"
    assert calibrated["training"]["class_balancing"].startswith("inverse-frequency")
    assert predict_model(calibrated, "OTP batao abhi")["scam_score"] > 0.5


def test_template_family_removes_greeting_and_number_variation() -> None:
    assert template_family("Namaste sir cab 3 minute mein pahunch raha hai") == template_family("Hello madam cab 9 minute mein pahunch raha hai")
