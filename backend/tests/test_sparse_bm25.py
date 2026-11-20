from pathlib import Path
from backend.app.models.document import DocumentChunk
from backend.app.services.retrieval.sparse_bm25 import BM25Retriever


def test_bm25_tokenization():
    tokens = BM25Retriever.tokenize("Administer Enoxaparin 40 mg subcutaneously for DVT prophylaxis!")
    assert "enoxaparin" in tokens
    assert "40" in tokens
    assert "mg" in tokens
    assert "prophylaxis" in tokens
    # Stopwords should be removed
    assert "for" not in tokens


def test_bm25_exact_term_and_dosage_retrieval():
    retriever = BM25Retriever()
    chunks = [
        DocumentChunk(
            id="CHK-MED-001",
            document_id="DOC-1",
            version_id="VER-1",
            chunk_index=0,
            page_number=1,
            section_heading="VTE Prophylaxis",
            text_content="Medical inpatients receive Enoxaparin 40 mg subcutaneous daily for VTE prophylaxis.",
            protected_text="",
            token_count=12,
            content_hash="h1",
        ),
        DocumentChunk(
            id="CHK-MED-002",
            document_id="DOC-1",
            version_id="VER-1",
            chunk_index=1,
            page_number=2,
            section_heading="Renal Dosing",
            text_content="If CrCl < 30 mL/min, reduce Enoxaparin to 30 mg subcutaneous once daily.",
            protected_text="",
            token_count=14,
            content_hash="h2",
        ),
        DocumentChunk(
            id="CHK-MED-003",
            document_id="DOC-2",
            version_id="VER-1",
            chunk_index=2,
            page_number=1,
            section_heading="AFib",
            text_content="Apixaban 5 mg twice daily or Rivaroxaban 20 mg daily with food.",
            protected_text="",
            token_count=13,
            content_hash="h3",
        ),
    ]

    retriever.index_chunks(chunks)
    assert retriever.get_total_indexed() == 3

    # Exact dosage query: 40 mg
    res1 = retriever.search("Enoxaparin 40 mg", top_k=2)
    assert len(res1) >= 1
    assert res1[0][0] == "CHK-MED-001"
    assert res1[0][1] == 1.0  # Top match normalized to 1.0

    # Exact renal dose query: 30 mg CrCl
    res2 = retriever.search("CrCl 30 mL/min Enoxaparin 30 mg", top_k=2)
    assert len(res2) >= 1
    assert res2[0][0] == "CHK-MED-002"

    # Completely irrelevant query
    res3 = retriever.search("Unrelated quantum physics formula string", top_k=2)
    assert len(res3) == 0


def test_bm25_persistence(tmp_path: Path):
    retriever = BM25Retriever()
    chunks = [
        DocumentChunk(
            id="CHK-BM-P1",
            document_id="DOC-P",
            version_id="VER-P",
            chunk_index=0,
            page_number=1,
            section_heading="Cardiology",
            text_content="Amiodarone 150 mg IV bolus over 10 minutes for ventricular tachycardia.",
            protected_text="",
            token_count=12,
            content_hash="hp",
        )
    ]
    retriever.index_chunks(chunks)
    save_file = str(tmp_path / "bm25_test.json")
    retriever.save(save_file)

    new_retriever = BM25Retriever()
    success = new_retriever.load(save_file)
    assert success is True
    assert new_retriever.get_total_indexed() == 1

    res = new_retriever.search("Amiodarone 150 mg tachycardia", top_k=1)
    assert len(res) == 1
    assert res[0][0] == "CHK-BM-P1"
