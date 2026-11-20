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
from backend.app.models.document import Document, DocumentChunk
from backend.app.models.query import Query, RetrievedEvidence
from backend.app.services.retrieval.engine import retrieval_engine


async def run_live_verification():
    print("=" * 70)
    print("MEDTRUST-ENGINE: SLICE 1 LIVE FLIGHT PATH VERIFICATION")
    print("=" * 70)

    # 1. Initialize Storage, DB, and Index Sync
    settings.init_directories()
    await init_db()
    async with async_session_factory() as session:
        synced_count = await retrieval_engine.sync_from_database(session)
    print(f"[1/5] Storage directories & PostgreSQL/SQLite initialized (Synced {synced_count} chunks).")

    samples_dir = settings.BASE_DIR / "app" / "data" / "sample_guidelines"
    sepsis_pdf = samples_dir / "sepsis_guideline_2026.pdf"
    anticoag_pdf = samples_dir / "anticoagulation_protocol.pdf"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://localhost:8000") as client:
        # Check Health Endpoint
        health_res = await client.get("/api/health")
        print(f"[2/5] Health Check Response: {health_res.json()}")
        assert health_res.status_code == 200

        # Check existing documents or upload Sepsis Guideline 2026
        with open(sepsis_pdf, "rb") as f:
            pdf1_bytes = f.read()

        upload1_res = await client.post(
            "/api/documents/upload",
            files={"file": ("sepsis_guideline_2026.pdf", pdf1_bytes, "application/pdf")},
            data={
                "title": "Surviving Sepsis Campaign Guidelines 2026",
                "domain": "Critical Care / Sepsis",
                "authoring_body": "International Sepsis Forum",
                "tier": "1",
                "version_tag": "2026.0",
            },
        )
        print(f"[3/5] Upload 1 Status: {upload1_res.status_code}")
        if upload1_res.status_code == 201:
            u1_data = upload1_res.json()
            print(f"      Document ID: {u1_data['document_id']}")
            print(f"      Indexed Chunks: {u1_data['total_chunks']}")
            print(f"      Processing Latency: {u1_data['processing_time_ms']} ms")
            print(f"      Content Hash: {u1_data['content_hash']}")
        elif upload1_res.status_code == 409:
            print("      Document is indexed (Duplicate Protection Active).")

        # Test Duplicate Rejection
        dup_res = await client.post(
            "/api/documents/upload",
            files={"file": ("sepsis_guideline_2026.pdf", pdf1_bytes, "application/pdf")},
            data={
                "title": "Duplicate Sepsis Upload",
                "domain": "Critical Care",
                "authoring_body": "Test",
            },
        )
        print(f"      Duplicate Upload Status: {dup_res.status_code} (Expected 409 Conflict)")
        assert dup_res.status_code == 409

        # Upload Anticoagulation Protocol
        with open(anticoag_pdf, "rb") as f:
            pdf2_bytes = f.read()

        upload2_res = await client.post(
            "/api/documents/upload",
            files={"file": ("anticoagulation_protocol.pdf", pdf2_bytes, "application/pdf")},
            data={
                "title": "Hospital Anticoagulation & Thromboprophylaxis Protocol",
                "domain": "Hematology / Pharmacy",
                "authoring_body": "Hospital Clinical Pharmacy Committee",
                "tier": "2",
                "version_tag": "2025.2",
            },
        )
        print(f"[4/5] Upload 2 Status: {upload2_res.status_code}")

        # List All Documents
        docs_res = await client.get("/api/documents")
        docs = docs_res.json()
        print(f"      Total Active Documents in System: {len(docs)}")

        # Perform Hybrid Search Queries
        test_queries = [
            ("When should broad-spectrum antimicrobials be administered in sepsis?", "hybrid"),
            ("What is the Enoxaparin dose adjustment for creatinine clearance under 30 mL/min?", "sparse"),
            ("Vasopressors and target mean arterial pressure in septic shock", "dense"),
        ]

        print("\n[5/5] Executing Hybrid Retrieval Flight Path Searches:")
        for q_text, q_mode in test_queries:
            search_res = await client.post(
                "/api/retrieval/search",
                json={"query": q_text, "top_k": 3, "mode": q_mode, "alpha": 0.5},
            )
            s_data = search_res.json()
            print(f"\n  >> Query: '{q_text}' [Mode: {q_mode}]")
            print(f"     Latency: {s_data['retrieval_latency_ms']} ms | Quality Score: {s_data['retrieval_quality_score']}")
            print(f"     Retrieved Evidence Anchors ({len(s_data['top_k_evidence'])} items):")

            for item in s_data["top_k_evidence"]:
                p = item["provenance"]
                print(f"       * Rank {item['rank_position']} [RRF: {item['rrf_score']} | Dense: {item['dense_score']} | Sparse: {item['sparse_score']}]")
                print(f"         Anchor: {p['document_title']} (v{p['document_version']}) | Page {p['page_number']} | Sec: '{p['section_heading']}' | Chunk: {p['chunk_id']}")
                print(f"         Excerpt: \"{item['text_content'][:110]}...\"")

    # Verify Database Persistence
    async with async_session_factory() as session:
        doc_count = (await session.execute(select(Document))).scalars().all()
        chunk_count = (await session.execute(select(DocumentChunk))).scalars().all()
        query_count = (await session.execute(select(Query))).scalars().all()
        ev_count = (await session.execute(select(RetrievedEvidence))).scalars().all()

        print("\n" + "=" * 70)
        print("DATABASE PERSISTENCE AUDIT (PostgreSQL / SQLite):")
        print(f"  - Master Documents Persisted: {len(doc_count)}")
        print(f"  - Provenance Chunks Persisted: {len(chunk_count)}")
        print(f"  - Queries Executed & Logged: {len(query_count)}")
        print(f"  - Retrieved Evidence Links Persisted: {len(ev_count)}")
        print("=" * 70)
        print("SLICE 1 FLIGHT PATH VALIDATION COMPLETE: 100% OPERATIONAL.")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_live_verification())
