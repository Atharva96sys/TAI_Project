import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin


class DocumentCollection(Base, TimestampMixin):
    """Logical grouping for clinical documents (e.g., Sepsis Protocols, Cardiology Guidelines)."""

    __tablename__ = "document_collections"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="collection", cascade="all, delete-orphan"
    )


class Document(Base, TimestampMixin):
    """Clinical Document master record with cryptographic hash integrity and provenance."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    collection_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("document_collections.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    domain: Mapped[str] = mapped_column(String(128), nullable=False, default="General Clinical")
    authoring_body: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Institutional Clinical Committee"
    )
    tier: Mapped[int] = mapped_column(Integer, default=1)  # 1=Official Guideline, 2=SOP, 3=Trial
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE"
    )  # ACTIVE, SUPERSEDED, QUARANTINED, FAILED
    total_pages: Mapped[int] = mapped_column(Integer, default=1)

    collection: Mapped[DocumentCollection | None] = relationship(
        "DocumentCollection", back_populates="documents"
    )
    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan"
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentVersion(Base, TimestampMixin):
    """Version tracking and lifecycle deprecation for clinical documents."""

    __tablename__ = "document_versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    version_tag: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")
    publication_date: Mapped[date] = mapped_column(
        Date, default=lambda: datetime.now(timezone.utc).date()
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    superseded_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("document_versions.id"), nullable=True
    )
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped[Document] = relationship("Document", back_populates="versions")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="version", cascade="all, delete-orphan"
    )


class DocumentChunk(Base, TimestampMixin):
    """Provenance-preserved structural passage/chunk extracted from a clinical document."""

    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )  # format: CHK-{doc_id_short}-{idx}
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    section_heading: Mapped[str] = mapped_column(String(255), nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    protected_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document: Mapped[Document] = relationship("Document", back_populates="chunks")
    version: Mapped[DocumentVersion] = relationship("DocumentVersion", back_populates="chunks")
