from backend.classifiers.taxonomy import detect_tactics


def tactic_names(text: str) -> set[str]:
    return {item["tactic"] for item in detect_tactics(text)}


def test_digital_arrest_tactics_are_explainable() -> None:
    names = tactic_names(
        "This is Inspector Rao from the cybercrime department. Your Aadhaar is linked "
        "to a money laundering case. Do not disconnect and transfer money immediately."
    )
    assert {"IDENTITY_CLAIM", "AUTHORITY_IMPERSONATION", "THREAT", "ISOLATION", "FINANCIAL_ACTION", "URGENCY"} <= names


def test_tamil_scam_is_functionally_detected() -> None:
    names = tactic_names(
        "சைபர் கிரைம் காவல் துறையிலிருந்து பேசுகிறேன். அழைப்பை துண்டிக்காதீர்கள். "
        "உடனே பாதுகாப்பான கணக்குக்கு பணம் அனுப்புங்கள்."
    )
    assert {"AUTHORITY_IMPERSONATION", "ISOLATION", "FINANCIAL_ACTION", "URGENCY"} <= names


def test_hinglish_credential_and_isolation_tactics() -> None:
    names = tactic_names("Call mat kaatna aur kisi ko mat batana. Abhi OTP batao warna account block hoga.")
    assert {"ISOLATION", "CREDENTIAL_REQUEST", "THREAT"} <= names


def test_hindi_native_script_variants_detect_full_attack_chain() -> None:
    names = tactic_names(
        "मुंबई पुलिस से बोल रहा हूं। आपके नाम पर गिरफ्तारी वारंट है। "
        "फोन मत रखिए, किसी से मत कहना और अभी यूपीआई से पैसे भेजिए।"
    )
    assert {"IDENTITY_CLAIM", "AUTHORITY_IMPERSONATION", "THREAT", "ISOLATION", "URGENCY", "FINANCIAL_ACTION"} <= names


def test_tamil_native_script_variants_detect_full_attack_chain() -> None:
    names = tactic_names(
        "சுங்க அதிகாரி பேசுகிறேன். உங்கள் கணக்கு முடக்கப்படும். அழைப்பை நிறுத்தாதீர்கள். "
        "இப்பொழுதே யுபிஐ மூலம் பணம் செலுத்துங்கள்."
    )
    assert {"IDENTITY_CLAIM", "AUTHORITY_IMPERSONATION", "THREAT", "ISOLATION", "URGENCY", "FINANCIAL_ACTION"} <= names


def test_hindi_and_tamil_safety_advice_do_not_trigger_credential_request() -> None:
    assert "CREDENTIAL_REQUEST" not in tactic_names("ओटीपी किसी के साथ साझा न करें।")
    assert "CREDENTIAL_REQUEST" not in tactic_names("ஓடிபியை யாரிடமும் பகிர வேண்டாம்.")


def test_normal_conversation_does_not_flag_social_engineering() -> None:
    assert not tactic_names("Could you bring the project notes to our meeting tomorrow morning?")
