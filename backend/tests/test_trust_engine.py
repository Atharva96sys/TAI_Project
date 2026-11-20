from backend.app.schemas.retrieval import EvidenceProvenance, RetrievedEvidenceItem
from backend.app.services.verification.trust_engine import TrustEngine


def test_trust_engine_fully_verified_response():
    evidence = [
        RetrievedEvidenceItem(
            chunk_id="CHK-SEPSIS-002",
            text_content="For adult patients with possible septic shock or a high likelihood of sepsis, we recommend administering broad-spectrum intravenous antimicrobials immediately, ideally within 1 hour of recognition.",
            dense_score=0.90,
            sparse_score=1.0,
            rrf_score=0.0163,
            rerank_score=0.95,
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

    response_text = "Administer broad-spectrum intravenous antimicrobials within 1 hour of recognition."
    eval_out = TrustEngine.evaluate(
        query="When to give antibiotics in sepsis?",
        response_text=response_text,
        evidence_anchors=evidence,
    )

    prof = eval_out.trust_profile
    assert prof.final_status == "VERIFIED"
    assert prof.evidence_coverage_pct == 100.0
    assert prof.mean_grounding_score >= 0.80
    assert prof.uncertainty_score < 0.35
    assert prof.human_review_required is False
    assert len(eval_out.verified_claims) == 1
    assert eval_out.verified_claims[0].status == "SUPPORTED"


def test_trust_engine_mixed_and_unsupported_claims():
    evidence = [
        RetrievedEvidenceItem(
            chunk_id="CHK-SEPSIS-002",
            text_content="For adult patients with possible septic shock, administer broad-spectrum IV antimicrobials within 1 hour of recognition.",
            dense_score=0.90,
            sparse_score=1.0,
            rrf_score=0.0163,
            rerank_score=0.95,
            rank_position=1,
            provenance=EvidenceProvenance(
                document_id="DOC-SEPSIS",
                document_title="Surviving Sepsis Clinical Guideline 2026",
                document_version="2026.0",
                page_number=2,
                section_heading="3.1 Antimicrobial Timing",
                chunk_id="CHK-SEPSIS-002",
                chunk_position=2,
                content_hash="h1",
                tier=1,
                authoring_body="International Sepsis Forum",
            ),
        )
    ]

    # Two claims: one supported, one completely fabricated
    response_text = (
        "[1] Administer broad-spectrum intravenous antimicrobials within 1 hour of recognition.\n"
        "[2] Continue antibiotic therapy empirically for 45 consecutive days."
    )
    eval_out = TrustEngine.evaluate(
        query="Antibiotic duration in sepsis",
        response_text=response_text,
        evidence_anchors=evidence,
    )

    prof = eval_out.trust_profile
    assert len(eval_out.verified_claims) == 2
    assert eval_out.verified_claims[0].status == "SUPPORTED"
    assert eval_out.verified_claims[1].status == "UNSUPPORTED"
    assert prof.evidence_coverage_pct == 50.0
    assert prof.final_status == "INSUFFICIENT_EVIDENCE"
    assert prof.human_review_required is True


def test_trust_engine_empty_evidence():
    eval_out = TrustEngine.evaluate(
        query="Unindexed disease protocol",
        response_text="Some ungrounded clinical text",
        evidence_anchors=[],
    )

    prof = eval_out.trust_profile
    assert prof.final_status == "INSUFFICIENT_EVIDENCE"
    assert prof.evidence_coverage_pct == 0.0
    assert prof.uncertainty_score == 1.0
    assert prof.human_review_required is True
    assert eval_out.is_insufficient_evidence is True
