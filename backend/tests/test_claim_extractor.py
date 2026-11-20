from backend.app.services.verification.claim_extractor import ClaimExtractor


def test_claim_extractor_numbered_list():
    raw_text = (
        "[1] Administer broad-spectrum intravenous antimicrobials within 1 hour of sepsis recognition.\n"
        "[2] De-escalate antimicrobial therapy daily based on pathogen identification.\n"
        "[3] Target a mean arterial pressure of 65 mmHg using Norepinephrine."
    )
    claims = ClaimExtractor.extract_claims(raw_text)
    assert len(claims) == 3
    assert "Administer broad-spectrum intravenous antimicrobials within 1 hour of sepsis recognition." in claims[0]
    assert "De-escalate antimicrobial therapy daily" in claims[1]
    assert "Target a mean arterial pressure of 65 mmHg" in claims[2]


def test_claim_extractor_preambles_and_compound_sentences():
    raw_text = (
        "According to the guidelines, medical inpatients should receive Enoxaparin 40 mg subcutaneous once daily. "
        "Furthermore, if creatinine clearance is under 30 mL/min, reduce Enoxaparin dose to 30 mg once daily."
    )
    claims = ClaimExtractor.extract_claims(raw_text)
    assert len(claims) >= 2
    # Preamble should be stripped
    assert not claims[0].lower().startswith("according to the guidelines")
    assert "Enoxaparin 40 mg" in claims[0]
    assert "30 mL/min" in claims[1] or "30 mg" in claims[1]


def test_claim_extractor_bullets():
    raw_text = (
        "- Apixaban 5 mg twice daily is recommended for atrial fibrillation.\n"
        "- Rivaroxaban 20 mg once daily should be taken with food."
    )
    claims = ClaimExtractor.extract_claims(raw_text)
    assert len(claims) == 2
    assert claims[0].startswith("Apixaban 5 mg")
    assert claims[1].startswith("Rivaroxaban 20 mg")
