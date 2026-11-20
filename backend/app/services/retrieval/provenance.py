from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.document import Document, DocumentChunk, DocumentVersion
from backend.app.schemas.retrieval import EvidenceProvenance, RetrievedEvidenceItem


class ProvenanceResolver:
    """Resolves and constructs verifiable EvidenceProvenance records from indexed database chunks."""

    @staticmethod
    async def resolve_evidence_items(
        session: AsyncSession,
        retrieved_raw_items: list[dict],
    ) -> list[RetrievedEvidenceItem]:
        """Fetch chunks and parent documents from PostgreSQL/SQLite to construct enriched RetrievedEvidenceItems."""
        if not retrieved_raw_items:
            return []

        chunk_ids = [item["chunk_id"] for item in retrieved_raw_items]
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.id.in_(chunk_ids))
            .options(
                selectinload(DocumentChunk.document),
                selectinload(DocumentChunk.version),
            )
        )
        result = await session.execute(stmt)
        chunk_map = {chunk.id: chunk for chunk in result.scalars().all()}

        enriched_items: list[RetrievedEvidenceItem] = []

        for item in retrieved_raw_items:
            cid = item["chunk_id"]
            chunk_obj = chunk_map.get(cid)
            if not chunk_obj:
                continue

            doc = chunk_obj.document
            ver = chunk_obj.version

            provenance = EvidenceProvenance(
                document_id=chunk_obj.document_id,
                document_title=doc.title if doc else "Clinical Document",
                document_version=ver.version_tag if ver else "1.0",
                page_number=chunk_obj.page_number,
                section_heading=chunk_obj.section_heading,
                chunk_id=chunk_obj.id,
                chunk_position=chunk_obj.chunk_index,
                content_hash=chunk_obj.content_hash,
                tier=doc.tier if doc else 1,
                authoring_body=doc.authoring_body if doc else "Institutional Clinical Committee",
            )

            enriched_items.append(
                RetrievedEvidenceItem(
                    chunk_id=chunk_obj.id,
                    text_content=chunk_obj.text_content,
                    dense_score=item.get("dense_score", 0.0),
                    sparse_score=item.get("sparse_score", 0.0),
                    rrf_score=item.get("rrf_score", 0.0),
                    rerank_score=item.get("rerank_score", 0.0),
                    rank_position=item.get("rank_position", 1),
                    provenance=provenance,
                )
            )

        return enriched_items
