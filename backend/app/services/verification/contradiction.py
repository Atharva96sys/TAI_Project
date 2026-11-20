import re
from dataclasses import dataclass
from backend.app.schemas.retrieval import RetrievedEvidenceItem


@dataclass
class ContradictionAnalysisResult:
    has_contradiction: bool
    contradiction_risk_score: float
    detected_conflicts: list[str]


class ContradictionDetector:
    """Detects guideline version discrepancies and inter-source clinical conflicts."""

    CONFLICT_PATTERNS = [
        # Vasopressor conflicts (Dopamine vs Norepinephrine)
        (
            r"\bdopamine\s+(?:is|as)\s+first[- ]line\b",
            r"\bnorepinephrine\s+(?:is|as)\s+first[- ](?:choice|line)\b",
            "Vasopressor Selection Conflict: Older recommendation (Dopamine) conflicts with first-line Norepinephrine recommendation.",
        ),
        # Antibiotic duration conflicts (e.g. 21-45 days vs 7-10 days)
        (
            r"(?:21|28|30|45)\s+days?\s+(?:of\s+)?(?:antibiotic|empiric|therapy)",
            r"(?:7\s+to\s+10\s+days?|shorter\s+courses?\s+of\s+7)",
            "Antibiotic Duration Conflict: Extended antibiotic duration conflicts with recommended 7-10 day de-escalation protocol.",
        ),
    ]

    @classmethod
    def analyze_evidence_set(
        cls,
        evidence_items: list[RetrievedEvidenceItem],
        generated_text: str | None = None,
        query: str | None = None,
    ) -> ContradictionAnalysisResult:
        """Scan retrieved evidence items and generated text for conflicting clinical directives."""
        if not evidence_items:
            return ContradictionAnalysisResult(
                has_contradiction=False,
                contradiction_risk_score=0.0,
                detected_conflicts=[],
            )

        detected_conflicts: list[str] = []

        # 1. Check for cross-version document collisions (e.g. 2024 vs 2026 guidelines retrieved simultaneously)
        doc_versions = {}
        for item in evidence_items:
            prov = item.provenance
            doc_id = prov.document_id
            if doc_id not in doc_versions:
                doc_versions[doc_id] = set()
            if prov.document_version:
                doc_versions[doc_id].add(prov.document_version)

        # Check if multiple versions of the same or related guideline are retrieved with conflicting topic content
        all_versions = {item.provenance.document_version for item in evidence_items if item.provenance.document_version}
        has_version_divergence = ("2024.1" in all_versions or "2024" in all_versions) and ("2026.0" in all_versions or "2026" in all_versions)

        if has_version_divergence:
            scope_text = f"{query or ''} {generated_text or ''}".lower()
            if any(k in scope_text for k in ["fluid", "resuscitation", "crystalloid", "30 ml/kg", "bolus", "volume"]):
                detected_conflicts.append(
                    "Guideline Version Collision: Retrieved evidence contains conflicting recommendations across Sepsis 2024 (fixed 30 mL/kg) and Sepsis 2026 (dynamic fluid assessment)."
                )

        # 2. Check for explicit semantic opposing assertions across chunks or text
        all_text = " \n ".join([item.text_content for item in evidence_items])
        if generated_text:
            all_text += f" \n {generated_text}"

        for pat_a, pat_b, conflict_desc in cls.CONFLICT_PATTERNS:
            match_a = re.search(pat_a, all_text, re.IGNORECASE)
            match_b = re.search(pat_b, all_text, re.IGNORECASE)
            if match_a and match_b:
                if conflict_desc not in detected_conflicts:
                    detected_conflicts.append(conflict_desc)

        has_conflict = len(detected_conflicts) > 0
        risk_score = 0.85 if has_conflict else 0.0

        return ContradictionAnalysisResult(
            has_contradiction=has_conflict,
            contradiction_risk_score=risk_score,
            detected_conflicts=detected_conflicts,
        )
