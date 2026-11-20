from __future__ import annotations

import re
from dataclasses import dataclass, field


# ──────────────────────────────────────────────────────────────────────────────
# Risk Tier Constants
# ──────────────────────────────────────────────────────────────────────────────

TIER_INFORMATIONAL = "INFORMATIONAL"
TIER_INTERPRETIVE = "INTERPRETIVE"
TIER_CLINICAL_RECOMMENDATION = "CLINICAL_RECOMMENDATION"
TIER_DOSAGE_TREATMENT = "DOSAGE_TREATMENT"
TIER_PATIENT_SPECIFIC = "PATIENT_SPECIFIC"

RISK_TIER_LEVELS: dict[str, int] = {
    TIER_INFORMATIONAL: 1,
    TIER_INTERPRETIVE: 2,
    TIER_CLINICAL_RECOMMENDATION: 3,
    TIER_DOSAGE_TREATMENT: 4,
    TIER_PATIENT_SPECIFIC: 5,
}

# Safety policy per tier
POLICY_PERMIT = "PERMIT"
POLICY_PERMIT_WITH_CAVEAT = "PERMIT_WITH_CAVEAT"
POLICY_REVIEW_REQUIRED = "REVIEW_REQUIRED"
POLICY_BLOCK = "BLOCK"

TIER_POLICY_MAP: dict[str, str] = {
    TIER_INFORMATIONAL: POLICY_PERMIT,
    TIER_INTERPRETIVE: POLICY_PERMIT,
    TIER_CLINICAL_RECOMMENDATION: POLICY_PERMIT_WITH_CAVEAT,
    TIER_DOSAGE_TREATMENT: POLICY_REVIEW_REQUIRED,
    TIER_PATIENT_SPECIFIC: POLICY_BLOCK,
}

CLINICAL_CAVEAT = (
    "⚠ CLINICAL DECISION-SUPPORT NOTICE: This response is generated from indexed "
    "clinical guidelines and is NOT a substitute for professional clinical judgment. "
    "Verify all recommendations against current authoritative sources and consult a "
    "licensed clinician before any patient care decision."
)

LOW_COVERAGE_THRESHOLD: float = 40.0  # pct below which evidence is 'low'

# ──────────────────────────────────────────────────────────────────────────────
# Pattern Libraries
# ──────────────────────────────────────────────────────────────────────────────

# TIER_5: Patient-Specific Indicators (HIPAA 18 Safe Harbor proxies)
_PII_PATTERNS: list[re.Pattern] = [
    # MRN / patient ID
    re.compile(r"\bMRN\b|\bpatient\s*(?:id|number|#)\b", re.IGNORECASE),
    # Date of birth
    re.compile(r"\bDOB\b|\bdate\s+of\s+birth\b|\bborn\s+(?:in|on)\b", re.IGNORECASE),
    # Names that suggest patient reference
    re.compile(r"\bfor\s+(?:my|the\s+)?patient\s+(?:[A-Z][a-z]+\s){1,3}", re.IGNORECASE),
    # Social security number
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    # Phone numbers
    re.compile(r"\b\d{3}[\s\-\.]\d{3}[\s\-\.]\d{4}\b"),
    # Explicit name reference
    re.compile(r"\bMr\.?\s+[A-Z][a-z]+\b|\bMrs\.?\s+[A-Z][a-z]+\b|\bDr\.?\s+[A-Z][a-z]+\b"),
    # Age + demographics
    re.compile(r"\b(?:\d{1,3}[-–]\s*year[-–]old\s+(?:male|female|man|woman|patient))\b", re.IGNORECASE),
]

# TIER_4: Dosage & Treatment — exact numeric clinical thresholds
_DOSAGE_PATTERNS: list[re.Pattern] = [
    # Drug name + dose (e.g. "Enoxaparin 40 mg", "Vancomycin 25 mg/kg")
    re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|µg|units?|IU|mEq|mmol|mL|L)\b(?:/\s*(?:kg|hr|min|day|dose))?", re.IGNORECASE),
    # Dosing frequency / route instructions
    re.compile(r"\b(?:dose|dosage|dosing|administer|infuse|inject|prescribe)\b", re.IGNORECASE),
    # IV / route specifications
    re.compile(r"\b(?:intravenous|subcutaneous|intramuscular|oral|sublingual|IV|SC|IM|PO|SQ)\b", re.IGNORECASE),
    # Creatinine clearance / renal dosing
    re.compile(r"\bcreatinine\s+clearance\b|\bCrCl\b|\brenal\s+(?:dosing|adjustment|impairment)\b", re.IGNORECASE),
    # Drug interactions
    re.compile(r"\binteract(?:ion)?s?\s+(?:with|between)\b|\bcontraindicated\b|\bside\s+effects?\b", re.IGNORECASE),
    # MAX dose safety boundary
    re.compile(r"\bmaximum\s+(?:dose|daily\s+dose)\b|\bdo\s+not\s+exceed\b", re.IGNORECASE),
]

# TIER_3: Clinical Recommendation signals
_RECOMMENDATION_PATTERNS: list[re.Pattern] = [
    # Guideline action verbs
    re.compile(r"\b(?:recommend(?:ed)?|guidelines?\s+(?:suggest|state|recommend)|first[- ]line|first[- ]choice|preferred\s+(?:agent|therapy|treatment))\b", re.IGNORECASE),
    # Treatment selection
    re.compile(r"\b(?:should\s+(?:we\s+)?(?:use|give|start|treat|administer)|which\s+(?:drug|agent|therapy|antibiotic|treatment|medication))\b", re.IGNORECASE),
    # Protocol queries
    re.compile(r"\b(?:protocol|regimen|guideline\s+for|treatment\s+for|management\s+of|management\s+protocol)\b", re.IGNORECASE),
    # Comparison/selection queries
    re.compile(r"\bversus\b|\bvs\.?\b|\bcompare\b|\bchoose\s+between\b|\bbetter\s+(?:option|choice)\b", re.IGNORECASE),
]

# TIER_2: Interpretive signals
_INTERPRETIVE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(?:how\s+does|mechanism\s+of|pathophysiology\s+of|why\s+does|explain|criteria\s+for|definition\s+of|what\s+is\s+the\s+(?:criteria|basis|rationale))\b", re.IGNORECASE),
    re.compile(r"\b(?:diagnostic\s+criteria|signs\s+of|symptoms\s+of|diagnosis\s+of|interpret(?:ation)?\s+of|classify|classification\s+of)\b", re.IGNORECASE),
]


# ──────────────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class QueryRiskAssessment:
    """Risk assessment result for a clinical query."""

    risk_tier: str
    tier_level: int
    policy: str
    pii_indicators_found: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    clinical_caveat: str | None = None
    should_block: bool = False
    human_review_required: bool = False
    review_reason: str | None = None
    evidence_override_triggered: bool = False

    @property
    def tier_display(self) -> str:
        return f"TIER_{self.tier_level} — {self.risk_tier}"


# ──────────────────────────────────────────────────────────────────────────────
# Query Risk Engine
# ──────────────────────────────────────────────────────────────────────────────

class QueryRiskEngine:
    """
    5-Tier Clinical Query Risk Classifier.

    Evaluates incoming clinical queries against escalating pattern libraries
    to determine appropriate safety policy actions.
    """

    @classmethod
    def assess(
        cls,
        query: str,
        evidence_coverage_pct: float = 100.0,
    ) -> QueryRiskAssessment:
        """
        Classify the clinical risk tier of a query and determine safety policy action.

        Args:
            query: Raw (pre-airlock) clinical query string.
            evidence_coverage_pct: Evidence coverage from Trust Engine (0.0–100.0).
                Used to override policy when evidence is low.

        Returns:
            QueryRiskAssessment with tier, policy, flags, and action directives.
        """
        flags: list[str] = []
        pii_found: list[str] = []

        # ── TIER 5 Check: Patient-Specific PII ───────────────────────────────
        for pattern in _PII_PATTERNS:
            m = pattern.search(query)
            if m:
                pii_found.append(m.group(0)[:80])

        if pii_found:
            return QueryRiskAssessment(
                risk_tier=TIER_PATIENT_SPECIFIC,
                tier_level=5,
                policy=POLICY_BLOCK,
                pii_indicators_found=pii_found,
                risk_flags=["Patient-specific query contains potential PHI/PII identifiers."],
                should_block=True,
                human_review_required=True,
                review_reason=(
                    f"Query contains {len(pii_found)} potential PHI indicator(s). "
                    "Blocked by Safety Policy to prevent Privacy Shield bypass."
                ),
            )

        # ── TIER 4 Check: Dosage & Treatment ─────────────────────────────────
        dosage_hits = sum(1 for p in _DOSAGE_PATTERNS if p.search(query))
        interaction_hit = bool(re.search(r"\b(?:drug\s+)?interact(?:ion)?s?\s+(?:with|between)\b|\bcontraindicated\b|\bcontraindications?\b", query, re.IGNORECASE))
        if dosage_hits >= 2 or interaction_hit:
            flags.append(
                f"Dosage/treatment patterns detected ({dosage_hits} indicators). "
                "Exact numeric clinical thresholds require human verification."
            )
            assessment = QueryRiskAssessment(
                risk_tier=TIER_DOSAGE_TREATMENT,
                tier_level=4,
                policy=POLICY_REVIEW_REQUIRED,
                risk_flags=flags,
                human_review_required=True,
                review_reason="Dosage/treatment query requires clinical pharmacist/physician review of exact numeric thresholds.",
            )
            return cls._apply_evidence_override(assessment, evidence_coverage_pct)

        # ── TIER 3 Check: Clinical Recommendation ────────────────────────────
        recommendation_hits = sum(1 for p in _RECOMMENDATION_PATTERNS if p.search(query))
        if recommendation_hits >= 1:
            flags.append(
                f"Clinical recommendation query detected ({recommendation_hits} indicators). "
                "Mandatory clinical disclaimer appended."
            )
            assessment = QueryRiskAssessment(
                risk_tier=TIER_CLINICAL_RECOMMENDATION,
                tier_level=3,
                policy=POLICY_PERMIT_WITH_CAVEAT,
                risk_flags=flags,
                clinical_caveat=CLINICAL_CAVEAT,
                human_review_required=False,
            )
            return cls._apply_evidence_override(assessment, evidence_coverage_pct)

        # ── TIER 2 Check: Interpretive ───────────────────────────────────────
        interpretive_hits = sum(1 for p in _INTERPRETIVE_PATTERNS if p.search(query))
        if interpretive_hits >= 1:
            flags.append(
                f"Interpretive/mechanism query detected ({interpretive_hits} indicators). "
                "Full response with guideline citations provided."
            )
            assessment = QueryRiskAssessment(
                risk_tier=TIER_INTERPRETIVE,
                tier_level=2,
                policy=POLICY_PERMIT,
                risk_flags=flags,
            )
            return cls._apply_evidence_override(assessment, evidence_coverage_pct)

        # ── TIER 1 Default: Informational ─────────────────────────────────────
        assessment = QueryRiskAssessment(
            risk_tier=TIER_INFORMATIONAL,
            tier_level=1,
            policy=POLICY_PERMIT,
            risk_flags=["Informational query — standard grounded response."],
        )
        return cls._apply_evidence_override(assessment, evidence_coverage_pct)

    @staticmethod
    def _apply_evidence_override(
        assessment: QueryRiskAssessment,
        evidence_coverage_pct: float,
    ) -> QueryRiskAssessment:
        """
        Override policy upward if evidence coverage is critically low.

        - If coverage == 0.0: policy forced to BLOCK (INSUFFICIENT_EVIDENCE state).
        - If coverage < LOW_COVERAGE_THRESHOLD (40%): escalate to REVIEW_REQUIRED.
        """
        if evidence_coverage_pct == 0.0 and assessment.policy != POLICY_BLOCK:
            assessment.evidence_override_triggered = True
            assessment.policy = POLICY_BLOCK
            assessment.human_review_required = True
            assessment.should_block = True
            assessment.risk_flags.append(
                "EVIDENCE OVERRIDE: No evidence anchors retrieved. "
                "Generation blocked — INSUFFICIENT_EVIDENCE state activated."
            )
            assessment.review_reason = (
                "Zero evidence retrieved. Query routed to Review Queue for human triage."
            )
        elif (
            evidence_coverage_pct < LOW_COVERAGE_THRESHOLD
            and assessment.policy in (POLICY_PERMIT, POLICY_PERMIT_WITH_CAVEAT)
        ):
            assessment.evidence_override_triggered = True
            assessment.policy = POLICY_REVIEW_REQUIRED
            assessment.human_review_required = True
            assessment.risk_flags.append(
                f"EVIDENCE OVERRIDE: Coverage {evidence_coverage_pct:.1f}% below threshold "
                f"({LOW_COVERAGE_THRESHOLD}%). Escalated to REVIEW_REQUIRED."
            )
            assessment.review_reason = (
                f"Low evidence coverage ({evidence_coverage_pct:.1f}%) for query. "
                "Requires human review before clinical use."
            )

        return assessment

    @staticmethod
    def get_tier_display_name(tier: str) -> str:
        level = RISK_TIER_LEVELS.get(tier, 0)
        return f"TIER {level} — {tier}"
