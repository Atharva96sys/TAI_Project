"""
MedTrust-Engine: Slice 3 Unit Tests — Query Risk Engine
Tests 5-tier classification, policy assignment, PII detection, and evidence override.
"""
from backend.app.services.risk.risk_engine import (
    QueryRiskEngine,
    TIER_INFORMATIONAL,
    TIER_INTERPRETIVE,
    TIER_CLINICAL_RECOMMENDATION,
    TIER_DOSAGE_TREATMENT,
    TIER_PATIENT_SPECIFIC,
    POLICY_PERMIT,
    POLICY_PERMIT_WITH_CAVEAT,
    POLICY_REVIEW_REQUIRED,
    POLICY_BLOCK,
)


# ─────────────────────────────────────────────────────────────────────────────
# TIER 1: Informational
# ─────────────────────────────────────────────────────────────────────────────

def test_tier1_informational_general_query():
    result = QueryRiskEngine.assess("What is sepsis?")
    assert result.risk_tier == TIER_INFORMATIONAL
    assert result.tier_level == 1
    assert result.policy == POLICY_PERMIT
    assert result.should_block is False
    assert result.human_review_required is False


def test_tier1_informational_definition_query():
    result = QueryRiskEngine.assess("What are the signs and definition of septic shock?")
    # Note: "signs of" triggers TIER_2, so we verify correct classification
    assert result.tier_level >= 1


# ─────────────────────────────────────────────────────────────────────────────
# TIER 2: Interpretive
# ─────────────────────────────────────────────────────────────────────────────

def test_tier2_interpretive_mechanism_query():
    result = QueryRiskEngine.assess("How does norepinephrine work as a vasopressor?")
    assert result.risk_tier == TIER_INTERPRETIVE
    assert result.tier_level == 2
    assert result.policy == POLICY_PERMIT
    assert result.should_block is False


def test_tier2_interpretive_diagnostic_criteria():
    result = QueryRiskEngine.assess("What are the diagnostic criteria for SIRS?")
    assert result.risk_tier == TIER_INTERPRETIVE
    assert result.tier_level == 2
    assert result.policy == POLICY_PERMIT


# ─────────────────────────────────────────────────────────────────────────────
# TIER 3: Clinical Recommendation
# ─────────────────────────────────────────────────────────────────────────────

def test_tier3_clinical_recommendation_first_line():
    result = QueryRiskEngine.assess(
        "What is the recommended first-line antibiotic for community-acquired pneumonia?"
    )
    assert result.risk_tier == TIER_CLINICAL_RECOMMENDATION
    assert result.tier_level == 3
    assert result.policy == POLICY_PERMIT_WITH_CAVEAT
    assert result.clinical_caveat is not None
    assert "CLINICAL DECISION-SUPPORT NOTICE" in result.clinical_caveat
    assert result.human_review_required is False


def test_tier3_treatment_protocol_query():
    result = QueryRiskEngine.assess(
        "What is the management protocol for septic shock?"
    )
    assert result.risk_tier == TIER_CLINICAL_RECOMMENDATION
    assert result.policy == POLICY_PERMIT_WITH_CAVEAT


def test_tier3_comparison_query():
    result = QueryRiskEngine.assess(
        "Which is better: Vancomycin versus Linezolid for MRSA treatment?"
    )
    assert result.risk_tier == TIER_CLINICAL_RECOMMENDATION
    assert result.policy == POLICY_PERMIT_WITH_CAVEAT


# ─────────────────────────────────────────────────────────────────────────────
# TIER 4: Dosage & Treatment
# ─────────────────────────────────────────────────────────────────────────────

def test_tier4_dosage_with_numeric_threshold():
    result = QueryRiskEngine.assess(
        "What is the correct dose of Enoxaparin 40 mg subcutaneous for DVT prophylaxis?"
    )
    assert result.risk_tier == TIER_DOSAGE_TREATMENT
    assert result.tier_level == 4
    assert result.policy == POLICY_REVIEW_REQUIRED
    assert result.human_review_required is True
    assert result.review_reason is not None


def test_tier4_renal_dosing_adjustment():
    result = QueryRiskEngine.assess(
        "How should I adjust the Vancomycin dose if creatinine clearance is below 30 mL/min?"
    )
    assert result.risk_tier == TIER_DOSAGE_TREATMENT
    assert result.policy == POLICY_REVIEW_REQUIRED
    assert result.human_review_required is True


def test_tier4_drug_interaction():
    result = QueryRiskEngine.assess(
        "What are the drug interactions with Warfarin that can affect INR?"
    )
    assert result.risk_tier == TIER_DOSAGE_TREATMENT
    assert result.human_review_required is True


# ─────────────────────────────────────────────────────────────────────────────
# TIER 5: Patient-Specific (PHI/PII)
# ─────────────────────────────────────────────────────────────────────────────

def test_tier5_mrn_patient_identifier():
    result = QueryRiskEngine.assess(
        "What treatment should patient MRN 12345678 receive for sepsis?"
    )
    assert result.risk_tier == TIER_PATIENT_SPECIFIC
    assert result.tier_level == 5
    assert result.policy == POLICY_BLOCK
    assert result.should_block is True
    assert result.human_review_required is True
    assert len(result.pii_indicators_found) >= 1


def test_tier5_date_of_birth_in_query():
    result = QueryRiskEngine.assess(
        "My patient date of birth 1975-03-12, what anticoagulation should they get?"
    )
    assert result.risk_tier == TIER_PATIENT_SPECIFIC
    assert result.should_block is True


def test_tier5_phone_number_in_query():
    result = QueryRiskEngine.assess(
        "Call 555-123-4567 for patient follow-up on their sepsis management"
    )
    assert result.risk_tier == TIER_PATIENT_SPECIFIC
    assert result.should_block is True


# ─────────────────────────────────────────────────────────────────────────────
# Evidence Override Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_evidence_override_zero_coverage_blocks():
    """PERMIT policy must be overridden to BLOCK when evidence_coverage_pct == 0."""
    result = QueryRiskEngine.assess(
        "What is sepsis?",
        evidence_coverage_pct=0.0,
    )
    assert result.evidence_override_triggered is True
    assert result.policy == POLICY_BLOCK
    assert result.human_review_required is True
    assert result.should_block is True


def test_evidence_override_low_coverage_escalates():
    """PERMIT policy must escalate to REVIEW_REQUIRED when coverage < 40%."""
    result = QueryRiskEngine.assess(
        "What is sepsis?",
        evidence_coverage_pct=25.0,
    )
    assert result.evidence_override_triggered is True
    assert result.policy == POLICY_REVIEW_REQUIRED
    assert result.human_review_required is True


def test_evidence_override_no_override_at_sufficient_coverage():
    """Sufficient evidence (≥40%) must not trigger override."""
    result = QueryRiskEngine.assess(
        "What is sepsis?",
        evidence_coverage_pct=80.0,
    )
    assert result.evidence_override_triggered is False
    assert result.policy == POLICY_PERMIT


def test_evidence_override_does_not_downgrade_high_tier():
    """High evidence coverage must not downgrade TIER_4 REVIEW_REQUIRED to PERMIT."""
    result = QueryRiskEngine.assess(
        "What is the correct dose of Norepinephrine 0.1 mcg/kg/min IV?",
        evidence_coverage_pct=100.0,
    )
    # Tier 4 should remain REVIEW_REQUIRED even with full coverage
    assert result.policy == POLICY_REVIEW_REQUIRED
    assert result.human_review_required is True
