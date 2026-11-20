from backend.app.schemas.retrieval import EvidenceProvenance, RetrievedEvidenceItem
from backend.app.services.verification.contradiction import ContradictionDetector


def test_contradiction_detection_sepsis_versions():
    evidence_items = [
        # Sepsis 2024 (Fixed 30 mL/kg for all)
        RetrievedEvidenceItem(
            chunk_id="CHK-2024-001",
            text_content="Administer at least 30 mL/kg of intravenous crystalloid fluid within the first 3 hours for all patients with hypotension regardless of cardiac ejection fraction.",
            dense_score=0.82,
            sparse_score=0.90,
            rrf_score=0.016,
            rerank_score=0.85,
            rank_position=1,
            provenance=EvidenceProvenance(
                document_id="DOC-2024",
                document_title="Sepsis Protocol 2024",
                document_version="2024.1",
                page_number=1,
                section_heading="Resuscitation Bundle",
                chunk_id="CHK-2024-001",
                chunk_position=1,
                content_hash="h2024",
                tier=2,
                authoring_body="Clinical SOP Group",
            ),
        ),
        # Sepsis 2026 (Dynamic assessment)
        RetrievedEvidenceItem(
            chunk_id="CHK-2026-003",
            text_content="For patients with sepsis-induced hypoperfusion or septic shock, we recommend dynamic fluid assessment rather than automatic fixed crystalloid loading.",
            dense_score=0.89,
            sparse_score=0.95,
            rrf_score=0.0163,
            rerank_score=0.92,
            rank_position=2,
            provenance=EvidenceProvenance(
                document_id="DOC-2026",
                document_title="Surviving Sepsis Clinical Guideline 2026",
                document_version="2026.0",
                page_number=3,
                section_heading="3.4 Fluid Resuscitation",
                chunk_id="CHK-2026-003",
                chunk_position=3,
                content_hash="h2026",
                tier=1,
                authoring_body="International Sepsis Forum",
            ),
        ),
    ]

    result = ContradictionDetector.analyze_evidence_set(evidence_items, query="fluid resuscitation protocol")
    assert result.has_contradiction is True
    assert result.contradiction_risk_score >= 0.80
    assert len(result.detected_conflicts) >= 1
    assert any("Version" in c or "Fluid" in c or "Conflict" in c for c in result.detected_conflicts)


def test_no_contradiction_consistent_evidence():
    evidence_items = [
        RetrievedEvidenceItem(
            chunk_id="CHK-VTE-001",
            text_content="Enoxaparin 40 mg subcutaneous once daily is recommended for VTE prophylaxis.",
            dense_score=0.85,
            sparse_score=0.90,
            rrf_score=0.016,
            rerank_score=0.88,
            rank_position=1,
            provenance=EvidenceProvenance(
                document_id="DOC-VTE",
                document_title="Anticoagulation Protocol",
                document_version="2025.2",
                page_number=1,
                section_heading="VTE",
                chunk_id="CHK-VTE-001",
                chunk_position=1,
                content_hash="h_vte",
                tier=2,
                authoring_body="Pharmacy Committee",
            ),
        )
    ]
    result = ContradictionDetector.analyze_evidence_set(evidence_items)
    assert result.has_contradiction is False
    assert result.contradiction_risk_score == 0.0
