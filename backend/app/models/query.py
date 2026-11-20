import uuid
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin


class Query(Base, TimestampMixin):
    """Clinical query submission with risk, telemetry, and execution tracking."""

    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"QRY-{uuid.uuid4().hex[:12]}"
    )
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_query_text: Mapped[str] = mapped_column(Text, nullable=False)
    protected_query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_risk_tier: Mapped[str] = mapped_column(
        String(32), default="INFORMATIONAL"
    )  # INFORMATIONAL, INTERPRETIVE, CLINICAL_RECOMMENDATION, DOSAGE_TREATMENT, PATIENT_SPECIFIC
    pii_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        String(32), default="COMPLETED"
    )  # COMPLETED, INSUFFICIENT_EVIDENCE, BLOCKED, REVIEW_REQUIRED, ERROR
    total_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)

    retrieved_evidence: Mapped[list["RetrievedEvidence"]] = relationship(
        "RetrievedEvidence", back_populates="query", cascade="all, delete-orphan"
    )


class RetrievedEvidence(Base, TimestampMixin):
    """Candidate evidence chunk retrieved for a query with granular scoring & fusion rank."""

    __tablename__ = "retrieved_evidence"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    query_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("queries.id", ondelete="CASCADE"), nullable=False
    )
    chunk_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False
    )
    dense_score: Mapped[float] = mapped_column(Float, default=0.0)
    sparse_score: Mapped[float] = mapped_column(Float, default=0.0)
    rrf_score: Mapped[float] = mapped_column(Float, default=0.0)
    rerank_score: Mapped[float] = mapped_column(Float, default=0.0)
    rank_position: Mapped[int] = mapped_column(Integer, default=1)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=True)

    query: Mapped[Query] = relationship("Query", back_populates="retrieved_evidence")
    chunk: Mapped["DocumentChunk"] = relationship("DocumentChunk")
