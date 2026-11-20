import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.models.query import Query, RetrievedEvidence
from backend.app.schemas.retrieval import RetrievalQueryRequest, RetrievalResponse
from backend.app.services.retrieval.engine import retrieval_engine
from backend.app.services.retrieval.provenance import ProvenanceResolver

router = APIRouter(prefix="/retrieval", tags=["Hybrid Retrieval & Evidence Anchors"])


@router.post(
    "/search",
    response_model=RetrievalResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Dense, Sparse, or Hybrid RRF retrieval and return provenance-anchored evidence",
)
async def search_evidence(
    req: RetrievalQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    start_time = time.perf_counter()

    if not req.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty.",
        )

    # 1. Execute Retrieval Engine Search
    raw_candidates = retrieval_engine.search(
        query=req.query,
        top_k=req.top_k,
        mode=req.mode,
        alpha=req.alpha,
    )

    # 2. Enrich with Full Provenance from PostgreSQL/SQLite
    enriched_evidence = await ProvenanceResolver.resolve_evidence_items(
        session=db,
        retrieved_raw_items=raw_candidates,
    )

    latency_ms = (time.perf_counter() - start_time) * 1000.0
    query_id = f"QRY-{uuid.uuid4().hex[:12]}"
    is_empty = len(enriched_evidence) == 0

    # 3. Compute Retrieval Quality Indicator
    quality_score = 0.0
    if enriched_evidence:
        quality_score = sum(e.rerank_score for e in enriched_evidence) / len(enriched_evidence)

    # 4. Persist Query and Retrieved Evidence in Database
    query_record = Query(
        id=query_id,
        raw_query_text=req.query,
        protected_query_text=req.query,  # Prepared for Slice 4 Privacy Shield
        query_risk_tier="INFORMATIONAL",  # Prepared for Slice 3 Risk Engine
        pii_count=0,
        status="COMPLETED" if not is_empty else "INSUFFICIENT_EVIDENCE",
        total_latency_ms=round(latency_ms, 2),
    )
    db.add(query_record)
    await db.flush()

    for item in enriched_evidence:
        evidence_record = RetrievedEvidence(
            query_id=query_id,
            chunk_id=item.chunk_id,
            dense_score=item.dense_score,
            sparse_score=item.sparse_score,
            rrf_score=item.rrf_score,
            rerank_score=item.rerank_score,
            rank_position=item.rank_position,
            is_selected=True,
        )
        db.add(evidence_record)

    await db.commit()

    return RetrievalResponse(
        query_id=query_id,
        query_text=req.query,
        mode=req.mode,
        total_candidates_retrieved=len(raw_candidates),
        top_k_evidence=enriched_evidence,
        retrieval_latency_ms=round(latency_ms, 2),
        retrieval_quality_score=round(quality_score, 4),
        is_empty_yield=is_empty,
    )


@router.get(
    "/stats",
    summary="Retrieve operational telemetry and index capacity",
)
async def get_retrieval_stats():
    return retrieval_engine.get_stats()
