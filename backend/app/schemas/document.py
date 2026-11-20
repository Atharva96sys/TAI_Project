from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class DocumentChunkRead(BaseModel):
    """Schema for individual document chunks with granular provenance."""

    id: str
    document_id: str
    version_id: str
    chunk_index: int
    page_number: int
    section_heading: str
    text_content: str
    protected_text: str
    token_count: int
    content_hash: str
    embedding_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentVersionRead(BaseModel):
    """Schema for document versions."""

    id: str
    document_id: str
    version_tag: str
    publication_date: date
    is_current: bool
    superseded_by_id: str | None = None
    changelog: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRead(BaseModel):
    """Schema for returning master document information."""

    id: str
    collection_id: str | None = None
    title: str
    filename: str
    file_size: int
    mime_type: str
    content_hash: str
    domain: str
    authoring_body: str
    tier: int
    status: str
    total_pages: int
    created_at: datetime
    updated_at: datetime
    versions: list[DocumentVersionRead] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    """Schema returned after a successful document ingestion and indexing."""

    document_id: str
    title: str
    filename: str
    status: str
    total_pages: int
    total_chunks: int
    content_hash: str
    processing_time_ms: float
    message: str


class DocumentCollectionCreate(BaseModel):
    """Schema for creating a collection."""

    name: str = Field(..., min_length=2, max_length=128)
    description: str | None = None


class DocumentCollectionRead(BaseModel):
    """Schema for reading a collection."""

    id: str
    name: str
    description: str | None = None
    created_at: datetime
    document_count: int = 0

    model_config = ConfigDict(from_attributes=True)
