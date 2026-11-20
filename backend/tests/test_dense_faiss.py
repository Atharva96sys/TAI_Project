from pathlib import Path
from backend.app.models.document import DocumentChunk
from backend.app.services.retrieval.dense_faiss import FAISSRetriever
from backend.app.services.retrieval.embeddings import embedding_provider


def test_faiss_dense_retrieval():
    retriever = FAISSRetriever(dimension=384)
    assert retriever.get_total_indexed() == 0

    # Create synthetic test chunks
    chunks = [
        DocumentChunk(
            id="CHK-SEPSIS-001",
            document_id="DOC-SEPSIS",
            version_id="VER-2026",
            chunk_index=0,
            page_number=2,
            section_heading="Antimicrobial Therapy",
            text_content="Administer broad-spectrum intravenous antimicrobials within 1 hour of sepsis recognition.",
            protected_text="",
            token_count=15,
            content_hash="hash1",
        ),
        DocumentChunk(
            id="CHK-SEPSIS-002",
            document_id="DOC-SEPSIS",
            version_id="VER-2026",
            chunk_index=1,
            page_number=3,
            section_heading="Vasopressors",
            text_content="Norepinephrine is the first-choice vasopressor to maintain a target MAP of 65 mmHg in septic shock.",
            protected_text="",
            token_count=18,
            content_hash="hash2",
        ),
        DocumentChunk(
            id="CHK-CARDIO-003",
            document_id="DOC-CARDIO",
            version_id="VER-2025",
            chunk_index=2,
            page_number=1,
            section_heading="Anticoagulation",
            text_content="Apixaban 5 mg twice daily is recommended for stroke prevention in non-valvular atrial fibrillation.",
            protected_text="",
            token_count=16,
            content_hash="hash3",
        ),
    ]

    indexed_count = retriever.index_chunks(chunks)
    assert indexed_count == 3
    assert retriever.get_total_indexed() == 3

    # Query 1: Sepsis antimicrobial therapy timing
    q1_vec = embedding_provider.embed_text("broad-spectrum antimicrobial therapy administration timing in sepsis")
    results1 = retriever.search(q1_vec, top_k=3)

    assert len(results1) == 3
    top_chunk_id, top_score = results1[0]
    assert top_chunk_id == "CHK-SEPSIS-001"
    assert top_score > 0.40

    # Query 2: Blood pressure / Vasopressor target
    q2_vec = embedding_provider.embed_text("Target mean arterial pressure and norepinephrine in septic shock")
    results2 = retriever.search(q2_vec, top_k=3)
    assert results2[0][0] == "CHK-SEPSIS-002"

    # Query 3: Atrial fibrillation blood thinner
    q3_vec = embedding_provider.embed_text("Apixaban dosage stroke prevention atrial fibrillation")
    results3 = retriever.search(q3_vec, top_k=3)
    assert results3[0][0] == "CHK-CARDIO-003"


def test_faiss_persistence(tmp_path: Path):
    retriever = FAISSRetriever(dimension=384)
    chunks = [
        DocumentChunk(
            id="CHK-PERSIST-001",
            document_id="DOC-01",
            version_id="VER-01",
            chunk_index=0,
            page_number=1,
            section_heading="Test",
            text_content="Hypoglycemia is managed with oral glucose or IV dextrose.",
            protected_text="",
            token_count=10,
            content_hash="hash_p",
        )
    ]
    retriever.index_chunks(chunks)
    assert retriever.get_total_indexed() == 1

    save_file = str(tmp_path / "test_faiss.bin")
    retriever.save(save_file)

    # Load in a fresh retriever
    new_retriever = FAISSRetriever(dimension=384)
    success = new_retriever.load(save_file)
    assert success is True
    assert new_retriever.get_total_indexed() == 1

    q_vec = embedding_provider.embed_text("glucose dextrose hypoglycemia")
    res = new_retriever.search(q_vec, top_k=1)
    assert len(res) == 1
    assert res[0][0] == "CHK-PERSIST-001"
