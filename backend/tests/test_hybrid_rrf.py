from backend.app.models.document import DocumentChunk
from backend.app.services.retrieval.dense_faiss import FAISSRetriever
from backend.app.services.retrieval.hybrid_rrf import HybridRetriever
from backend.app.services.retrieval.sparse_bm25 import BM25Retriever


def test_hybrid_rrf_scoring_and_fusion():
    v_retriever = FAISSRetriever(dimension=384)
    s_retriever = BM25Retriever()

    chunks = [
        DocumentChunk(
            id="CHK-SEPSIS-ABX",
            document_id="DOC-SEPSIS",
            version_id="VER-2026",
            chunk_index=0,
            page_number=2,
            section_heading="Antimicrobial Timing",
            text_content="Administer broad-spectrum intravenous antimicrobials within 1 hour of sepsis recognition.",
            protected_text="",
            token_count=14,
            content_hash="h1",
        ),
        DocumentChunk(
            id="CHK-SEPSIS-VASO",
            document_id="DOC-SEPSIS",
            version_id="VER-2026",
            chunk_index=1,
            page_number=3,
            section_heading="Vasopressors",
            text_content="Norepinephrine infusion titrated to target a mean arterial pressure of 65 mmHg in septic shock.",
            protected_text="",
            token_count=16,
            content_hash="h2",
        ),
        DocumentChunk(
            id="CHK-SEPSIS-FLUID",
            document_id="DOC-SEPSIS",
            version_id="VER-2026",
            chunk_index=2,
            page_number=3,
            section_heading="Fluid Resuscitation",
            text_content="Dynamic fluid assessment with conservative 30 mL/kg balanced crystalloids within 3 hours.",
            protected_text="",
            token_count=15,
            content_hash="h3",
        ),
    ]

    v_retriever.index_chunks(chunks)
    s_retriever.index_chunks(chunks)

    hybrid = HybridRetriever(
        vector_retriever=v_retriever,
        sparse_retriever=s_retriever,
        rrf_k=60,
        default_alpha=0.5,
    )

    # 1. Hybrid Search for Antibiotics in Sepsis
    results = hybrid.retrieve(
        query="When should broad-spectrum antimicrobials be administered for sepsis?",
        top_k=3,
        mode="hybrid",
        alpha=0.5,
    )

    assert len(results) >= 1
    top_hit = results[0]
    assert top_hit["chunk_id"] == "CHK-SEPSIS-ABX"
    assert top_hit["rank_position"] == 1
    assert top_hit["rrf_score"] > 0.0
    assert top_hit["dense_score"] > 0.0
    assert top_hit["sparse_score"] > 0.0

    # 2. Mode 'dense' only
    dense_only = hybrid.retrieve(
        query="Norepinephrine MAP 65 mmHg septic shock",
        top_k=2,
        mode="dense",
    )
    assert len(dense_only) == 2
    assert dense_only[0]["chunk_id"] == "CHK-SEPSIS-VASO"
    assert dense_only[0]["dense_score"] > 0.0
    assert dense_only[0]["sparse_score"] == 0.0

    # 3. Mode 'sparse' only
    sparse_only = hybrid.retrieve(
        query="Norepinephrine MAP 65 mmHg",
        top_k=2,
        mode="sparse",
    )
    assert len(sparse_only) >= 1
    assert sparse_only[0]["chunk_id"] == "CHK-SEPSIS-VASO"
    assert sparse_only[0]["sparse_score"] > 0.0
    assert sparse_only[0]["dense_score"] == 0.0

    # 4. Zero yield on nonsensical query in sparse
    empty_res = hybrid.retrieve(
        query="xyzqqq999nonexistentclinicalterm",
        top_k=3,
        mode="sparse",
    )
    assert len(empty_res) == 0
