"""
MedTrust-Engine: Review Queue ORM Model (Slice 3)
Human-in-the-loop oversight station for clinician adjudication.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin


class ReviewQueueItem(Base, TimestampMixin):
    """
    Represents a clinical query/response that has been flagged for human review.

    State Machine:
        PENDING → UNDER_REVIEW → APPROVED | REJECTED | ESCALATED → (terminal)
        PENDING → DISMISSED (terminal)
    """

    __tablename__ = "review_queue"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"RVW-{uuid.uuid4().hex[:12]}"
    )

    # Origin references
    query_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("queries.id", ondelete="CASCADE"), nullable=False
    )
    response_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("generated_responses.id", ondelete="SET NULL"), nullable=True
    )

    # Risk classification that triggered this review
    risk_tier: Mapped[str] = mapped_column(String(64), nullable=False, default="CLINICAL_RECOMMENDATION")
    review_reason: Mapped[str] = mapped_column(Text, nullable=False)
    trust_profile_summary: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # State Machine
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="PENDING"
    )  # PENDING, UNDER_REVIEW, APPROVED, REJECTED, ESCALATED, DISMISSED

    # Routing metadata
    is_auto_routed: Mapped[bool] = mapped_column(Boolean, default=True)
    enqueued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Reviewer decision fields
    reviewer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    query: Mapped["Query"] = relationship("Query")  # type: ignore[name-defined]
    response: Mapped["GeneratedResponse | None"] = relationship("GeneratedResponse")  # type: ignore[name-defined]
