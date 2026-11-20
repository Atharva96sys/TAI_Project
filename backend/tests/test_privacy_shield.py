import pytest
from backend.app.services.privacy.shield import PrivacyShield


def test_clean_text_no_pii():
    text = "Administer broad-spectrum intravenous antimicrobials within 1 hour."
    res = PrivacyShield.scan_and_pseudonymize(text)
    assert res.has_pii is False
    assert res.total_redactions == 0
    assert res.protected_text == text


def test_hipaa_18_identifiers_detection_and_pseudonymization():
    raw = (
        "Patient Alice Smith, MRN-884910, phone 555-014-9922, email asmith@hospital.org, "
        "DOB 1982-05-12, SSN 000-12-3456, residing at 123 Health Boulevard, ZIP 94107."
    )
    res = PrivacyShield.scan_and_pseudonymize(raw)
    assert res.has_pii is True
    assert res.total_redactions >= 5
    assert "[MRN_001]" in res.protected_text
    assert "884910" not in res.protected_text
    assert "000-12-3456" not in res.protected_text
    assert "asmith@hospital.org" not in res.protected_text

    # Verify token map integrity
    assert "[MRN_001]" in res.token_map
    assert res.token_map["[MRN_001]"] == "884910"


def test_reversible_pseudonymization():
    raw = "Consultation for patient Marcus Vance with MRN-998811 regarding sepsis."
    res = PrivacyShield.scan_and_pseudonymize(raw)
    assert res.has_pii is True
    assert "[MRN_001]" in res.protected_text

    restored = PrivacyShield.restore_tokens(res.protected_text, res.token_map)
    assert "998811" in restored
    assert "Marcus Vance" in restored
