from backend.asr.local_whisper import ASR_PROMPTS


def test_multilingual_asr_prompts_include_high_value_security_terms() -> None:
    assert {"en", "hi", "ta", "hinglish"} <= set(ASR_PROMPTS)
    assert "ओटीपी" in ASR_PROMPTS["hi"]
    assert "ஓடிபி" in ASR_PROMPTS["ta"]
