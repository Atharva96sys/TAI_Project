from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.retrieval import RetrievedEvidenceItem


class ClaimEvidenceLinkRead(BaseModel):
    """Evidence anchor link for a verified claim."""

    id: str
    chunk_id: str
    entailment_score: float
    citation_page: int
    citation_section: str
    document_title: str | None = None
    document_version: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ClaimRead(BaseModel):
    """Schema for an atomic verified claim with grounding state and evidence anchors."""

    id: str
    claim_index: int
    claim_text: str
    status: str  # SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, UNABLE_TO_VERIFY
    grounding_score: float
    contradiction_score: float = 0.0
    explanation: str | None = None
    evidence_links: list[ClaimEvidenceLinkRead] = []

    model_config = ConfigDict(from_attributes=True)


class TrustProfileRead(BaseModel):
    """Multi-dimensional Trust Profile according to the MedTrust Trust Model."""

    evidence_coverage_pct: float = Field(..., ge=0.0, le=100.0, description="Percentage of claims grounded in evidence")
    mean_grounding_score: float = Field(..., ge=0.0, le=1.0, description="Average NLI entailment score across claims")
    retrieval_quality_score: float = Field(..., ge=0.0, le=1.0, description="Average quality score of evidence anchors")
    source_quality_tier: str = Field("HIGH (Peer-reviewed Guideline)", description="Source authority classification")
    contradiction_risk: str = Field("LOW", description="Source discrepancy risk (LOW, MODERATE, HIGH)")
    privacy_risk: str = Field("LOW", description="Privacy/PHI exposure level")
    security_risk: str = Field("CLEAR", description="Security airlock screening status")
    query_risk_tier: str = Field("CLINICAL_RECOMMENDATION", description="Query risk classification")
    uncertainty_score: float = Field(..., ge=0.0, le=1.0, description="Residual epistemic uncertainty indicator")
    final_status: str = Field(..., description="Operational status (VERIFIED, PARTIALLY_VERIFIED, INSUFFICIENT_EVIDENCE, CONTRADICTORY, REVIEW_REQUIRED, BLOCKED)")
    human_review_required: bool = False


class GenerateAndVerifyRequest(BaseModel):
    """Request to execute end-to-end grounded generation and claim verification."""

    query: str = Field(..., min_length=2, max_length=2000, description="Clinical query string")
    top_k: int = Field(5, ge=1, le=20, description="Number of evidence anchors to retrieve")
    mode: str = Field("hybrid", pattern="^(hybrid|dense|sparse)$")
    alpha: float = Field(0.5, ge=0.0, le=1.0)
    model_provider: str | None = Field(None, description="Optional LLM provider override")


class VerifyTextRequest(BaseModel):
    """Request to verify arbitrary clinical text against indexed evidence."""

    text_to_verify: str = Field(..., min_length=5, max_length=5000, description="Clinical text containing claims")
    query_context: str | None = Field(None, description="Optional originating query context")
    top_k: int = Field(5, ge=1, le=20)


class VerificationResponse(BaseModel):
    """Comprehensive response with answer, claim-by-claim verification, Trust Profile, and evidence."""

    query_id: str
    response_id: str
    query_text: str
    response_text: str
    trust_profile: TrustProfileRead
    claims: list[ClaimRead]
    evidence_anchors: list[RetrievedEvidenceItem]
    is_insufficient_evidence: bool = False
    contradictions_detected: list[str] = []
    total_latency_ms: float = 0.0
    generated_at: datetime = Field(default_factory=datetime.utcnow)
