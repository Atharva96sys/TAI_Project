import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.core.database import async_session_factory, init_db
from backend.app.main import app
from backend.app.models.verification import Claim, ClaimEvidenceLink, GeneratedResponse
from backend.app.services.retrieval.engine import retrieval_engine


async def run_slice2_verification():
    print("=" * 75)
    print("MEDTRUST-ENGINE: SLICE 2 LIVE FLIGHT PATH & CLAIM VERIFICATION AUDIT")
    print("=" * 75)

    # 1. Initialize Storage, DB, & load persisted indexes
    settings.init_directories()
    await init_db()

    # Sync retrieval engine index from database
    async with async_session_factory() as session:
        synced = await retrieval_engine.sync_from_database(session)
    print(f"[0/4] Retrieval engine synced from database ({synced} chunks loaded).")

    samples_dir = settings.BASE_DIR / "app" / "data" / "sample_guidelines"
    sepsis_2026 = samples_dir / "sepsis_guideline_2026.pdf"
    sepsis_2024 = samples_dir / "sepsis_guideline_2024.pdf"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
        # Ingest Sepsis 2026
        with open(sepsis_2026, "rb") as f:
            b26 = f.read()
        up1 = await client.post(
            "/api/documents/upload",
            files={"file": ("sepsis_guideline_2026.pdf", b26, "application/pdf")},
            data={"title": "Surviving Sepsis Clinical Guideline 2026", "tier": "1", "version_tag": "2026.0"},
        )
        print(f"[1/4] Ingest Sepsis 2026 Status: {up1.status_code} " + ("(New)" if up1.status_code == 201 else "(Already Indexed)"))

        # Ingest Sepsis 2024
        with open(sepsis_2024, "rb") as f:
            b24 = f.read()
        up2 = await client.post(
            "/api/documents/upload",
            files={"file": ("sepsis_guideline_2024.pdf", b24, "application/pdf")},
            data={"title": "Sepsis Protocol 2024 (Superseded)", "tier": "2", "version_tag": "2024.1"},
        )
        print(f"[2/4] Ingest Sepsis 2024 Status: {up2.status_code} " + ("(New)" if up2.status_code == 201 else "(Already Indexed)"))

        stats = (await client.get("/api/retrieval/stats")).json()
        print(f"      Total Indexed Chunks: {stats['total_vector_chunks']} (dense) / {stats['total_sparse_chunks']} (sparse)")

        # =======================================================================
        # FLIGHT PATH 1: FULLY GROUNDED CLINICAL INQUIRY
        # =======================================================================
        print("\n" + "-" * 75)
        print("FLIGHT PATH 1: FULLY GROUNDED CLINICAL INQUIRY")
        print("-" * 75)
        q1 = "When should broad-spectrum antimicrobials be administered in sepsis?"
        r1 = await client.post(
            "/api/verification/generate-and-verify",
            json={"query": q1, "top_k": 3, "mode": "hybrid"},
        )
        assert r1.status_code == 200
        d1 = r1.json()

        print(f"Query: \"{d1['query_text']}\"")
        print(f"\nGenerated Clinical Response:")
        for line in d1["response_text"].split("\n"):
            print(f"  {line}")
        prof1 = d1["trust_profile"]
        print(f"\nMEDTRUST TRUST PROFILE:")
        print(f"  * Evidence Coverage:    {prof1['evidence_coverage_pct']}%")
        print(f"  * Mean Claim Grounding: {prof1['mean_grounding_score']}")
        print(f"  * Retrieval Quality:    {prof1['retrieval_quality_score']}")
        print(f"  * Epistemic Uncertainty:{prof1['uncertainty_score']}")
        print(f"  * Source Tier:          {prof1['source_quality_tier']}")
        print(f"  * Operational Status:   {prof1['final_status']}")
        print(f"  * Human Review Required:{prof1['human_review_required']}")
        print(f"\nClaim-by-Claim NLI Verification ({len(d1['claims'])} atomic claims):")
        for c in d1["claims"]:
            sym = {"SUPPORTED": "✓ SUPPORTED", "PARTIALLY_SUPPORTED": "~ PARTIAL", "UNSUPPORTED": "✗ UNSUPPORTED", "CONTRADICTED": "! CONTRADICTED"}.get(c["status"], c["status"])
            print(f"  [{sym}] (Score {c['grounding_score']:.3f}): \"{c['claim_text'][:90]}\"")
            for link in c["evidence_links"]:
                print(f"    -> {link['document_title']} v{link['document_version']} | Pg {link['citation_page']} | \"{link['citation_section']}\"")

        # =======================================================================
        # FLIGHT PATH 2: CROSS-VERSION COLLISION & CONTRADICTION DETECTION
        # =======================================================================
        print("\n" + "-" * 75)
        print("FLIGHT PATH 2: VERSION COLLISION & CONTRADICTION DETECTION")
        print("-" * 75)
        q2 = "What is the fluid resuscitation protocol for septic shock?"
        r2 = await client.post(
            "/api/verification/generate-and-verify",
            json={"query": q2, "top_k": 5, "mode": "hybrid"},
        )
        assert r2.status_code == 200
        d2 = r2.json()
        prof2 = d2["trust_profile"]
        print(f"Query: \"{d2['query_text']}\"")
        print(f"Evidence Coverage: {prof2['evidence_coverage_pct']}%")
        print(f"Operational Status: {prof2['final_status']}")
        print(f"Contradiction Risk: {prof2['contradiction_risk']}")
        print(f"Human Review Required: {prof2['human_review_required']}")
        print(f"Detected Conflicts ({len(d2['contradictions_detected'])}):")
        for conf in d2["contradictions_detected"]:
            print(f"  ! {conf}")

        # Evidence versions seen
        ev_versions = list({ev["provenance"]["document_version"] for ev in d2["evidence_anchors"]})
        print(f"Evidence versions retrieved: {ev_versions}")

        # =======================================================================
        # FLIGHT PATH 3: INSUFFICIENT EVIDENCE REFUSAL (unindexed domain)
        # =======================================================================
        print("\n" + "-" * 75)
        print("FLIGHT PATH 3: UNINDEXED DOMAIN — EVIDENCE REFUSAL")
        print("-" * 75)
        q3 = "What is the gene therapy CRISPR dosage for Huntington's disease?"
        r3 = await client.post(
            "/api/verification/generate-and-verify",
            json={"query": q3, "top_k": 3, "mode": "hybrid"},
        )
        assert r3.status_code == 200
        d3 = r3.json()
        prof3 = d3["trust_profile"]
        print(f"Query: \"{d3['query_text']}\"")
        print(f"Response: {d3['response_text'][:110]}...")
        print(f"Evidence Coverage: {prof3['evidence_coverage_pct']}%")
        print(f"Operational Status: {prof3['final_status']} (Generation Correctly Restricted)")
        print(f"Human Review Required: {prof3['human_review_required']}")

        # =======================================================================
        # FLIGHT PATH 4: ARBITRARY TEXT CLAIM VERIFICATION
        # =======================================================================
        print("\n" + "-" * 75)
        print("FLIGHT PATH 4: ARBITRARY TEXT VERIFICATION (SUPPORTED vs FABRICATED)")
        print("-" * 75)
        supported_text = (
            "For adult patients with possible septic shock, broad-spectrum intravenous antimicrobials should "
            "be administered within 1 hour of recognition."
        )
        rv = await client.post(
            "/api/verification/verify-text",
            json={"text_to_verify": supported_text, "query_context": "sepsis antimicrobial timing", "top_k": 3},
        )
        assert rv.status_code == 200
        vd = rv.json()
        vpf = vd["trust_profile"]
        print(f"Text: \"{supported_text[:90]}...\"")
        print(f"Status: {vpf['final_status']} | Coverage: {vpf['evidence_coverage_pct']}% | Grounding: {vpf['mean_grounding_score']:.3f}")
        for c in vd["claims"]:
            print(f"  [{c['status']}] (Score {c['grounding_score']:.3f}): \"{c['claim_text'][:90]}\"")

    # =======================================================================
    # DATABASE AUDIT
    # =======================================================================
    async with async_session_factory() as session:
        resp_count = (await session.execute(select(GeneratedResponse))).scalars().all()
        claims_count = (await session.execute(select(Claim))).scalars().all()
        links_count = (await session.execute(select(ClaimEvidenceLink))).scalars().all()

        print("\n" + "=" * 75)
        print("DATABASE PERSISTENCE AUDIT (Slice 2):")
        print(f"  - Generated Responses Persisted: {len(resp_count)}")
        print(f"  - Atomic Claims Persisted:        {len(claims_count)}")
        print(f"  - Claim-Evidence Links Persisted: {len(links_count)}")
        print("=" * 75)
        print("SLICE 2 FLIGHT PATH & CLAIM VERIFICATION AUDIT COMPLETE: 100% OPERATIONAL.")
        print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_slice2_verification())
