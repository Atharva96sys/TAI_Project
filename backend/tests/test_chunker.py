import hashlib
from pathlib import Path
from backend.app.services.ingestion.chunker import SemanticChunker
from backend.app.services.ingestion.parser import DocumentParser


def test_chunking_provenance_preservation(sample_guidelines_dir: Path):
    pdf_path = sample_guidelines_dir / "sepsis_guideline_2026.pdf"
    with open(pdf_path, "rb") as f:
        content = f.read()

    parsed = DocumentParser.parse(
        content=content,
        filename="sepsis_guideline_2026.pdf",
        mime_type="application/pdf",
    )

    doc_id = "doc-test-12345678-uuid"
    version_id = "ver-test-87654321-uuid"

    chunks = SemanticChunker.chunk_document(
        parsed_doc=parsed,
        document_id=doc_id,
        version_id=version_id,
        chunk_size_tokens=100,
        overlap_tokens=20,
    )

    assert len(chunks) >= 3

    for idx, chunk in enumerate(chunks):
        assert chunk.document_id == doc_id
        assert chunk.version_id == version_id
        assert chunk.chunk_index == idx
        assert chunk.page_number in [1, 2, 3]
        assert len(chunk.section_heading) > 0
        assert len(chunk.text_content.strip()) > 0
        assert chunk.token_count > 0
        assert chunk.id.startswith(f"CHK-{doc_id[:8]}-")

        # Verify content hash integrity
        expected_hash = hashlib.sha256(chunk.text_content.encode("utf-8")).hexdigest()
        assert chunk.content_hash == expected_hash

    # Check page 2 chunk contains antibiotic timing
    p2_chunks = [c for c in chunks if c.page_number == 2]
    assert len(p2_chunks) > 0
    assert any("within 1 hour" in c.text_content for c in p2_chunks)

    # Check page 3 chunk contains Norepinephrine
    p3_chunks = [c for c in chunks if c.page_number == 3]
    assert len(p3_chunks) > 0
    assert any("Norepinephrine" in c.text_content for c in p3_chunks)
