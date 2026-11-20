import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin


class SecurityEvent(Base, TimestampMixin):
    """Logs adversarial attempts, direct/indirect prompt injection, and policy security trips."""

    __tablename__ = "security_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"SEC-{uuid.uuid4().hex[:10]}"
    )
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # DIRECT_INJECTION, INDIRECT_INJECTION, JAILBREAK_ATTEMPT, DELIMITER_BREAKOUT
    threat_level: Mapped[str] = mapped_column(
        String(32), nullable=False, default="HIGH"
    )  # LOW, MEDIUM, HIGH, CRITICAL
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="QUERY"
    )  # QUERY, DOCUMENT, RETRIEVED_CHUNK
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detected_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    action_taken: Mapped[str] = mapped_column(
        String(32), nullable=False, default="BLOCKED"
    )  # BLOCKED, QUARANTINED, SANITIZED, MONITORED


class PrivacyEvent(Base, TimestampMixin):
    """Tracks HIPAA 18 PII/PHI detection and pseudonymization incidents."""

    __tablename__ = "privacy_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"PRV-{uuid.uuid4().hex[:10]}"
    )
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="QUERY"
    )  # QUERY, DOCUMENT, RETRIEVED_CHUNK
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # MRN, PATIENT_NAME, DATE_OF_BIRTH, PHONE, EMAIL, SSN, ADDRESS
    masked_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    redacted_token: Mapped[str] = mapped_column(String(64), nullable=False)
