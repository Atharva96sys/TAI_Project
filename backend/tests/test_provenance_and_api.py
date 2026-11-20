import io
from pathlib import Path
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.document import Document, DocumentChunk
from backend.app.models.query import Query, RetrievedEvidence


@pytest.mark.asyncio
async def test_end_to_end_ingestion_retrieval_provenance(
    client: AsyncClient,
    test_db: AsyncSession,
    sample_guidelines_dir: Path,
):
    pdf_path = sample_guidelines_dir / "sepsis_guideline_2026.pdf"
    assert pdf_path.exists()

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # 1. Upload and Ingest Document via API
    files = {
        "file": ("sepsis_guideline_2026.pdf", pdf_bytes, "application/pdf")
    }
    data = {
        "title": "Surviving Sepsis Clinical Guideline 2026",
        "domain": "Critical Care / Sepsis",
        "authoring_body": "International Sepsis Forum",
        "tier": "1",
        "version_tag": "2026.0",
    }

    upload_resp = await client.post("/api/documents/upload", files=files, data=data)
    assert upload_resp.status_code == 201
    upload_data = upload_resp.json()

    doc_id = upload_data["document_id"]
    assert upload_data["title"] == "Surviving Sepsis Clinical Guideline 2026"
    assert upload_data["total_pages"] == 3
    assert upload_data["total_chunks"] >= 3
    assert len(upload_data["content_hash"]) == 64
    assert upload_data["processing_time_ms"] > 0

    # 2. Verify Duplicate Document Rejection (409 Conflict)
    dup_files = {
        "file": ("sepsis_guideline_2026.pdf", pdf_bytes, "application/pdf")
    }
    dup_resp = await client.post("/api/documents/upload", files=dup_files, data=data)
    assert dup_resp.status_code == 409
    assert "Duplicate document rejected" in dup_resp.json()["detail"]

    # 3. List Documents API
    list_resp = await client.get("/api/documents")
    assert list_resp.status_code == 200
    docs_list = list_resp.json()
    assert len(docs_list) >= 1
    assert any(d["id"] == doc_id for d in docs_list)

    # 4. Inspect Document Chunks with Granular Provenance
    chunks_resp = await client.get(f"/api/documents/{doc_id}/chunks")
    assert chunks_resp.status_code == 200
    chunks_list = chunks_resp.json()
    assert len(chunks_list) >= 3

    for chunk in chunks_list:
        assert chunk["document_id"] == doc_id
        assert chunk["page_number"] in [1, 2, 3]
        assert len(chunk["section_heading"]) > 0
        assert len(chunk["content_hash"]) == 64

    # 5. Execute Hybrid Search Query with Provenance Verification
    query_payload = {
        "query": "What is the recommended antimicrobial timing for sepsis?",
        "top_k": 3,
        "mode": "hybrid",
        "alpha": 0.5,
    }

    search_resp = await client.post("/api/retrieval/search", json=query_payload)
    assert search_resp.status_code == 200
    search_data = search_resp.json()

    assert search_data["is_empty_yield"] is False
    assert len(search_data["top_k_evidence"]) >= 1
    assert search_data["retrieval_latency_ms"] > 0
    assert search_data["retrieval_quality_score"] > 0

    # Check Top Evidence Anchor Provenance
    top_hit = search_data["top_k_evidence"][0]
    prov = top_hit["provenance"]

    assert prov["document_id"] == doc_id
    assert prov["document_title"] == "Surviving Sepsis Clinical Guideline 2026"
    assert prov["document_version"] == "2026.0"
    assert prov["page_number"] == 2
    assert "antimicrobial" in top_hit["text_content"].lower()
    assert any("1 hour" in h["text_content"] for h in search_data["top_k_evidence"])
    assert top_hit["rank_position"] == 1
    assert top_hit["dense_score"] > 0
    assert top_hit["sparse_score"] > 0
    assert top_hit["rrf_score"] > 0

    # 6. Verify Database Persistence of Query and Evidence
    query_id = search_data["query_id"]
    q_stmt = select(Query).where(Query.id == query_id)
    q_res = await test_db.execute(q_stmt)
    saved_query = q_res.scalar_one_or_none()
    assert saved_query is not None
    assert saved_query.raw_query_text == query_payload["query"]

    ev_stmt = select(RetrievedEvidence).where(RetrievedEvidence.query_id == query_id)
    ev_res = await test_db.execute(ev_stmt)
    saved_evidence = ev_res.scalars().all()
    assert len(saved_evidence) >= 1
    assert saved_evidence[0].chunk_id == top_hit["chunk_id"]

    # 7. Check Retrieval Stats API
    stats_resp = await client.get("/api/retrieval/stats")
    assert stats_resp.status_code == 200
    stats_data = stats_resp.json()
    assert stats_data["total_vector_chunks"] >= 3
    assert stats_data["total_sparse_chunks"] >= 3


@pytest.mark.asyncio
async def test_empty_query_validation(client: AsyncClient):
    resp = await client.post("/api/retrieval/search", json={"query": "   ", "top_k": 5})
    assert resp.status_code == 422 or resp.status_code == 400
