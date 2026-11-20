from backend.app.schemas.retrieval import EvidenceProvenance, RetrievedEvidenceItem
from backend.app.services.verification.nli_matcher import NLIMatcher


def test_nli_matcher_supported_claim():
    evidence = [
        RetrievedEvidenceItem(
            chunk_id="CHK-SEPSIS-002",
            text_content="For adult patients with possible septic shock or a high likelihood of sepsis, we recommend administering broad-spectrum intravenous antimicrobials immediately, ideally within 1 hour of recognition.",
            dense_score=0.88,
            sparse_score=1.0,
            rrf_score=0.0163,
            rerank_score=0.94,
            rank_position=1,
            provenance=EvidenceProvenance(
                document_id="DOC-SEPSIS",
                document_title="Surviving Sepsis Clinical Guideline 2026",
                document_version="2026.0",
                page_number=2,
                section_heading="3.1 Antimicrobial Administration Timing",
                chunk_id="CHK-SEPSIS-002",
                chunk_position=2,
                content_hash="h1",
                tier=1,
                authoring_body="International Sepsis Forum",
            ),
        )
    ]

    # Supported Claim
    claim_text = "Administer broad-spectrum intravenous antimicrobials within 1 hour of sepsis recognition."
    res = NLIMatcher.verify_claim(1, claim_text, evidence)

    assert res.status == "SUPPORTED"
    assert res.grounding_score >= 0.80
    assert res.best_evidence_link is not None
    assert res.best_evidence_link.chunk_id == "CHK-SEPSIS-002"
    assert res.best_evidence_link.citation_page == 2


def test_nli_matcher_unsupported_claim():
    evidence = [
        RetrievedEvidenceItem(
            chunk_id="CHK-SEPSIS-002",
            text_content="For adult patients with possible septic shock or a high likelihood of sepsis, we recommend administering broad-spectrum intravenous antimicrobials immediately, ideally within 1 hour of recognition.",
            dense_score=0.88,
            sparse_score=1.0,
            rrf_score=0.0163,
            rerank_score=0.94,
            rank_position=1,
            provenance=EvidenceProvenance(
                document_id="DOC-SEPSIS",
                document_title="Surviving Sepsis Clinical Guideline 2026",
                document_version="2026.0",
                page_number=2,
                section_heading="3.1 Antimicrobial Administration Timing",
                chunk_id="CHK-SEPSIS-002",
                chunk_position=2,
                content_hash="h1",
                tier=1,
                authoring_body="International Sepsis Forum",
            ),
        )
    ]

    # Unsupported / Fabricated Claim (Gene therapy for Alzheimer's disease)
    claim_text = "Administer CRISPR gene therapy weekly for advanced Alzheimer's disease dementia."
    res = NLIMatcher.verify_claim(2, claim_text, evidence)

    assert res.status == "UNSUPPORTED"
    assert res.grounding_score < 0.50
