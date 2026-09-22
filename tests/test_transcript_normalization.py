from backend.service import ScamTraceService
from backend.utils.transcript import normalize_security_terms


def test_security_term_normalizer_corrects_common_asr_spacing() -> None:
    normalized, corrections = normalize_security_terms(
        "Tell me the o t p and c v v. Use u p i after installing any desk."
    )
    assert normalized == "Tell me the OTP and CVV. Use UPI after installing AnyDesk."
    assert {item["to"] for item in corrections} >= {"OTP", "CVV", "UPI", "AnyDesk"}


def test_normalized_spelling_reaches_tactic_detection() -> None:
    service = ScamTraceService()
    result = service.analyze_text("Tell me the o t p now and transfer using u p i.", "en")
    tactics = {item["tactic"] for item in result["tactics"]}
    assert {"CREDENTIAL_REQUEST", "FINANCIAL_ACTION"} <= tactics
    assert result["transcript"]["corrections"]
    assert result["fusion"]["level"] in {"HIGH", "CRITICAL"}
