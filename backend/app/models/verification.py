import uuid
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin


class GeneratedResponse(Base, TimestampMixin):
    """Clinical AI synthesized response with calculated Trust Profile and telemetry."""

    __tablename__ = "generated_responses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"RSP-{uuid.uuid4().hex[:12]}"
    )
    query_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("queries.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    model_provider: Mapped[str] = mapped_column(String(64), nullable=False, default="DeterministicClinicalEngine")
    model_name: Mapped[str] = mapped_column(String(64), nullable=False, default="clinical-grounding-v1")
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Trust Profile Indicators
    evidence_coverage_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    mean_grounding_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    retrieval_quality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    uncertainty_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    contradiction_risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Token & Execution Telemetry
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    generation_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    verification_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Final Operational Decision Status
    final_status: Mapped[str] = mapped_column(
        String(32), default="VERIFIED"
    )  # VERIFIED, PARTIALLY_VERIFIED, INSUFFICIENT_EVIDENCE, CONTRADICTORY, REVIEW_REQUIRED, BLOCKED, ERROR

    query: Mapped["Query"] = relationship("Query")
    claims: Mapped[list["Claim"]] = relationship(
        "Claim", back_populates="response", cascade="all, delete-orphan", order_by="Claim.claim_index"
    )


class Claim(Base, TimestampMixin):
    """Atomic declarative factual assertion decomposed from generated clinical response."""

    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"CLM-{uuid.uuid4().hex[:10]}"
    )
    response_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("generated_responses.id", ondelete="CASCADE"), nullable=False
    )
    claim_index: Mapped[int] = mapped_column(Integer, nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="SUPPORTED"
    )  # SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, UNABLE_TO_VERIFY
    grounding_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    contradiction_score: Mapped[float] = mapped_column(Float, default=0.0)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    response: Mapped[GeneratedResponse] = relationship("GeneratedResponse", back_populates="claims")
    evidence_links: Mapped[list["ClaimEvidenceLink"]] = relationship(
        "ClaimEvidenceLink", back_populates="claim", cascade="all, delete-orphan"
    )


class ClaimEvidenceLink(Base, TimestampMixin):
    """Ties an atomic claim to an exact retrieved evidence anchor."""

    __tablename__ = "claim_evidence_links"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    claim_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False
    )
    evidence_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("retrieved_evidence.id", ondelete="SET NULL"), nullable=True
    )
    chunk_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False
    )
    entailment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    citation_page: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    citation_section: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    claim: Mapped[Claim] = relationship("Claim", back_populates="evidence_links")
    chunk: Mapped["DocumentChunk"] = relationship("DocumentChunk")
