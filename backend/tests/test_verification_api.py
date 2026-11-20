from pathlib import Path
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.verification import Claim, ClaimEvidenceLink, GeneratedResponse


@pytest.mark.asyncio
async def test_end_to_end_generate_and_verify_api(
    client: AsyncClient,
    test_db: AsyncSession,
    sample_guidelines_dir: Path,
):
    pdf_path = sample_guidelines_dir / "sepsis_guideline_2026.pdf"
    assert pdf_path.exists()

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # 1. Ingest Clinical Document
    files = {"file": ("sepsis_guideline_2026.pdf", pdf_bytes, "application/pdf")}
    data = {
        "title": "Surviving Sepsis Clinical Guideline 2026",
        "domain": "Critical Care / Sepsis",
        "authoring_body": "International Sepsis Forum",
        "tier": "1",
        "version_tag": "2026.0",
    }
    upload_resp = await client.post("/api/documents/upload", files=files, data=data)
    assert upload_resp.status_code == 201

    # 2. Execute Grounded Generation & Claim Verification
    gen_payload = {
        "query": "When should broad-spectrum antimicrobials be administered in sepsis?",
        "top_k": 3,
        "mode": "hybrid",
        "alpha": 0.5,
    }

    verify_resp = await client.post("/api/verification/generate-and-verify", json=gen_payload)
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()

    response_id = v_data["response_id"]
    query_id = v_data["query_id"]
    assert response_id.startswith("RSP-")
    assert query_id.startswith("QRY-")

    # Verify Trust Profile
    prof = v_data["trust_profile"]
    assert prof["evidence_coverage_pct"] >= 75.0
    assert prof["final_status"] in ["VERIFIED", "PARTIALLY_VERIFIED"]
    assert prof["mean_grounding_score"] > 0.60
    assert prof["uncertainty_score"] < 0.50

    # Verify Claims Breakdown
    claims = v_data["claims"]
    assert len(claims) >= 1
    assert any("antimicrobial" in c["claim_text"].lower() or "1 hour" in c["claim_text"] for c in claims)
    assert any(c["status"] == "SUPPORTED" for c in claims)

    # Check evidence link on top claim
    top_claim = [c for c in claims if c["status"] == "SUPPORTED"][0]
    assert len(top_claim["evidence_links"]) >= 1
    link = top_claim["evidence_links"][0]
    assert link["citation_page"] == 2
    assert "3.1" in link["citation_section"] or "ANTIMICROBIAL" in link["citation_section"].upper()

    # 3. Database Persistence Verification
    stmt = select(GeneratedResponse).where(GeneratedResponse.id == response_id)
    res = await test_db.execute(stmt)
    saved_response = res.scalar_one_or_none()
    assert saved_response is not None
    assert saved_response.query_id == query_id
    assert saved_response.evidence_coverage_pct == prof["evidence_coverage_pct"]

    claim_stmt = select(Claim).where(Claim.response_id == response_id)
    claim_res = await test_db.execute(claim_stmt)
    saved_claims = claim_res.scalars().all()
    assert len(saved_claims) == len(claims)

    link_stmt = select(ClaimEvidenceLink).where(ClaimEvidenceLink.claim_id == saved_claims[0].id)
    link_res = await test_db.execute(link_stmt)
    saved_links = link_res.scalars().all()
    assert len(saved_links) >= 1

    # 4. Fetch Response via GET API
    get_resp = await client.get(f"/api/verification/{response_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["response_id"] == response_id
    assert len(get_data["claims"]) == len(claims)


@pytest.mark.asyncio
async def test_verify_arbitrary_text_unsupported_claim(
    client: AsyncClient,
    sample_guidelines_dir: Path,
):
    pdf_path = sample_guidelines_dir / "sepsis_guideline_2026.pdf"
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    await client.post(
        "/api/documents/upload",
        files={"file": ("sepsis_guideline_2026.pdf", pdf_bytes, "application/pdf")},
        data={"title": "Sepsis Guideline", "tier": "1"},
    )

    # Verify a fabricated, unsupported clinical assertion
    fake_text = "Administer experimental mRNA nanoparticle infusion for Sepsis."
    verify_resp = await client.post(
        "/api/verification/verify-text",
        json={"text_to_verify": fake_text, "query_context": "Sepsis mRNA therapy"},
    )
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()

    assert v_data["trust_profile"]["final_status"] == "INSUFFICIENT_EVIDENCE"
    assert v_data["claims"][0]["status"] in ["UNSUPPORTED", "PARTIALLY_SUPPORTED"]
    assert v_data["claims"][0]["grounding_score"] <= 0.60
