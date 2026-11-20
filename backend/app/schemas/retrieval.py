from pydantic import BaseModel, Field


class RetrievalQueryRequest(BaseModel):
    """Schema for submitting a retrieval query."""

    query: str = Field(..., min_length=2, max_length=2000, description="Clinical query string")
    collection_id: str | None = Field(None, description="Optional collection filter")
    top_k: int = Field(5, ge=1, le=50, description="Number of evidence anchors to return")
    mode: str = Field("hybrid", pattern="^(hybrid|dense|sparse)$", description="Retrieval mode")
    alpha: float = Field(0.5, ge=0.0, le=1.0, description="RRF balance (1.0=dense, 0.0=sparse)")


class EvidenceProvenance(BaseModel):
    """Detailed provenance metadata for a retrieved evidence anchor."""

    document_id: str
    document_title: str
    document_version: str
    page_number: int
    section_heading: str
    chunk_id: str
    chunk_position: int
    content_hash: str
    tier: int
    authoring_body: str


class RetrievedEvidenceItem(BaseModel):
    """A single retrieved evidence anchor with detailed score breakdown and provenance."""

    chunk_id: str
    text_content: str
    dense_score: float
    sparse_score: float
    rrf_score: float
    rerank_score: float
    rank_position: int
    provenance: EvidenceProvenance


class RetrievalResponse(BaseModel):
    """Response containing retrieved evidence anchors, retrieval metrics, and query telemetry."""

    query_id: str
    query_text: str
    mode: str
    total_candidates_retrieved: int
    top_k_evidence: list[RetrievedEvidenceItem]
    retrieval_latency_ms: float
    retrieval_quality_score: float
    is_empty_yield: bool
