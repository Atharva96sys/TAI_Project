import uuid
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin


class AuditEvent(Base, TimestampMixin):
    """Cryptographically chained rolling-hash audit ledger entry for clinical governance."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"AUD-{uuid.uuid4().hex[:12]}"
    )
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # QUERY_PROCESSED, DOCUMENT_INGESTED, SECURITY_THREAT_BLOCKED, PRIVACY_REDACTION, CLINICAL_REVIEW_DECISION
    actor_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default="SYSTEM"
    )  # SYSTEM, CLINICIAN, REVIEWER
    query_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    prev_chain_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    current_chain_hash: Mapped[str] = mapped_column(String(64), nullable=False)
