import time
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models.document import Document, DocumentChunk, DocumentCollection, DocumentVersion
from backend.app.schemas.document import (
    DocumentChunkRead,
    DocumentRead,
    DocumentUploadResponse,
)
from backend.app.services.ingestion.chunker import SemanticChunker
from backend.app.services.ingestion.parser import DocumentParser, IngestionError
from backend.app.services.retrieval.engine import retrieval_engine

router = APIRouter(prefix="/documents", tags=["Document Intelligence & Provenance"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload, validate, parse, chunk, and index a clinical guideline PDF/document",
)
async def upload_document(
    file: UploadFile = File(..., description="Clinical document (PDF, Markdown, or Text)"),
    title: str = Form(..., description="Formal clinical guideline/document title"),
    domain: str = Form("General Clinical", description="Clinical specialty/domain"),
    authoring_body: str = Form(
        "Institutional Clinical Committee", description="Authoring organization"
    ),
    tier: int = Form(1, ge=1, le=3, description="Authority tier (1=Official, 2=SOP, 3=Trial)"),
    version_tag: str = Form("1.0", description="Semantic version tag (e.g. 2026.1)"),
    collection_id: str | None = Form(None, description="Optional collection ID"),
    db: AsyncSession = Depends(get_db),
):
    start_time = time.perf_counter()
    filename = file.filename or "uploaded_document"

    # Read file content safely
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file payload: {str(e)}",
        )

    # Validate and Parse document with PyMuPDF
    try:
        parsed_doc = DocumentParser.parse(
            content=content,
            filename=filename,
            mime_type=file.content_type,
        )
    except IngestionError as ie:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ie))
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document parsing failure for '{filename}': {str(ex)}",
        )

    # Check for Duplicate Documents via Content Hash
    duplicate_stmt = select(Document).where(Document.content_hash == parsed_doc.content_hash)
    dup_res = await db.execute(duplicate_stmt)
    existing_doc = dup_res.scalar_one_or_none()
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate document rejected. An identical document ('{existing_doc.title}', ID: {existing_doc.id}) with content hash '{parsed_doc.content_hash}' is already indexed.",
        )

    # Save document file to disk storage
    doc_id = str(uuid.uuid4())
    save_path = settings.DOCUMENTS_DIR / f"{doc_id}_{Path(filename).name}"
    try:
        with open(save_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document to file store: {str(e)}",
        )

    # Create Document and Version ORM entities
    new_doc = Document(
        id=doc_id,
        collection_id=collection_id,
        title=title,
        filename=filename,
        file_path=str(save_path),
        file_size=parsed_doc.file_size,
        mime_type=parsed_doc.mime_type,
        content_hash=parsed_doc.content_hash,
        domain=domain,
        authoring_body=authoring_body,
        tier=tier,
        status="ACTIVE",
        total_pages=parsed_doc.total_pages,
    )

    # ── SECURITY AIRLOCK SCAN: Check for Indirect Document Injection ──
    full_doc_text = " \n ".join([p.text for p in parsed_doc.pages])
    from backend.app.services.security.airlock import SecurityAirlock
    from backend.app.services.privacy.shield import PrivacyShield
    from backend.app.services.governance.audit_ledger import CryptographicAuditLedger

    sec_scan = SecurityAirlock.scan_document_text(full_doc_text, document_title=title)
    if not sec_scan.is_safe:
        new_doc.status = "QUARANTINED"
        db.add(new_doc)
        await db.flush()

        await SecurityAirlock.log_security_event(
            session=db,
            event_type="INDIRECT_INJECTION",
            threat_level=sec_scan.threat_level,
            source_type="DOCUMENT",
            source_id=doc_id,
            detected_pattern=sec_scan.detected_pattern or "Adversarial text injection",
            action_taken="QUARANTINED",
        )
        await CryptographicAuditLedger.append_event(
            session=db,
            event_type="DOCUMENT_QUARANTINED",
            actor_id="SECURITY_AIRLOCK",
            document_id=doc_id,
            payload={"reason": sec_scan.threat_category, "title": title},
        )
        await db.commit()
        await db.refresh(new_doc)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return DocumentUploadResponse(
            document_id=doc_id,
            title=new_doc.title,
            filename=new_doc.filename,
            status="QUARANTINED",
            total_pages=new_doc.total_pages,
            total_chunks=0,
            content_hash=new_doc.content_hash,
            processing_time_ms=round(latency_ms, 2),
            message=f"SECURITY AIRLOCK: Document '{new_doc.title}' quarantined due to detected injection attempt.",
        )

    db.add(new_doc)
    await db.flush()

    # ── PRIVACY SHIELD SCAN: Check for PHI in Document ──────────────
    priv_scan = PrivacyShield.scan_and_pseudonymize(full_doc_text)
    if priv_scan.has_pii:
        await PrivacyShield.log_privacy_events(
            session=db,
            source_type="DOCUMENT",
            source_id=doc_id,
            entities=priv_scan.entities_detected,
        )

    ver_id = str(uuid.uuid4())
    new_ver = DocumentVersion(
        id=ver_id,
        document_id=doc_id,
        version_tag=version_tag,
        is_current=True,
        changelog=f"Initial ingestion of {filename}",
    )
    db.add(new_ver)
    await db.flush()

    # Generate Provenance-Preserved Chunks
    chunks = SemanticChunker.chunk_document(
        parsed_doc=parsed_doc,
        document_id=doc_id,
        version_id=ver_id,
        chunk_size_tokens=settings.CHUNK_SIZE_TOKENS,
        overlap_tokens=settings.CHUNK_OVERLAP_TOKENS,
    )

    for chunk in chunks:
        db.add(chunk)

    # Index in FAISS and BM25
    retrieval_engine.index_document_chunks(chunks)

    await CryptographicAuditLedger.append_event(
        session=db,
        event_type="DOCUMENT_INGESTED",
        actor_id="INGESTION_SERVICE",
        document_id=doc_id,
        payload={"title": title, "version": version_tag, "chunks_count": len(chunks)},
    )

    await db.commit()
    await db.refresh(new_doc)

    latency_ms = (time.perf_counter() - start_time) * 1000.0

    return DocumentUploadResponse(
        document_id=doc_id,
        title=new_doc.title,
        filename=new_doc.filename,
        status=new_doc.status,
        total_pages=new_doc.total_pages,
        total_chunks=len(chunks),
        content_hash=new_doc.content_hash,
        processing_time_ms=round(latency_ms, 2),
        message=f"Successfully indexed '{new_doc.title}' across {len(chunks)} provenance chunks in FAISS and BM25.",
    )


@router.get("", response_model=list[DocumentRead], summary="List all indexed clinical documents")
async def list_documents(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Document)
        .options(selectinload(Document.versions))
        .order_by(Document.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/{document_id}", response_model=DocumentRead, summary="Get document metadata by ID")
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Document)
        .where(Document.id == document_id)
        .options(selectinload(Document.versions))
    )
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    return doc


@router.get(
    "/{document_id}/chunks",
    response_model=list[DocumentChunkRead],
    summary="Inspect all provenance chunks for a document",
)
async def get_document_chunks(document_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
    )
    res = await db.execute(stmt)
    chunks = res.scalars().all()
    if not chunks:
        # Check if doc exists
        doc_stmt = select(Document).where(Document.id == document_id)
        doc_res = await db.execute(doc_stmt)
        if not doc_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID '{document_id}' not found.",
            )
    return chunks
