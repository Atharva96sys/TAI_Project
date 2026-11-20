from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.document import DocumentChunk
from backend.app.services.retrieval.dense_faiss import FAISSRetriever
from backend.app.services.retrieval.hybrid_rrf import HybridRetriever
from backend.app.services.retrieval.sparse_bm25 import BM25Retriever


class RetrievalEngine:
    """Central manager orchestrating FAISS vector index, BM25 term index, and Hybrid RRF."""

    def __init__(self, index_dir: Path = settings.INDEX_DIR):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.faiss_path = str(self.index_dir / "faiss_index.bin")
        self.bm25_path = str(self.index_dir / "bm25_index.json")

        self.vector_retriever = FAISSRetriever(dimension=settings.EMBEDDING_DIMENSION)
        self.sparse_retriever = BM25Retriever()
        self.hybrid_retriever = HybridRetriever(
            vector_retriever=self.vector_retriever,
            sparse_retriever=self.sparse_retriever,
            rrf_k=settings.RRF_K,
            default_alpha=settings.RRF_ALPHA,
        )

        # Attempt to load pre-existing indexes on disk
        self.load_indexes()

    def clear(self) -> None:
        """Reset internal vector and sparse indices to empty state."""
        self.vector_retriever = FAISSRetriever(dimension=settings.EMBEDDING_DIMENSION)
        self.sparse_retriever = BM25Retriever()
        self.hybrid_retriever = HybridRetriever(
            vector_retriever=self.vector_retriever,
            sparse_retriever=self.sparse_retriever,
            rrf_k=settings.RRF_K,
            default_alpha=settings.RRF_ALPHA,
        )

    def index_document_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Add new chunks to both FAISS and BM25 indices and persist."""
        if not chunks:
            return 0

        v_count = self.vector_retriever.index_chunks(chunks)
        s_count = self.sparse_retriever.index_chunks(chunks)

        # Persist index snapshots to disk
        self.save_indexes()
        return max(v_count, s_count)

    async def sync_from_database(self, session: AsyncSession) -> int:
        """Synchronize in-memory FAISS and BM25 indices with persistent DocumentChunks in DB."""
        stmt = select(DocumentChunk).order_by(DocumentChunk.chunk_index.asc())
        result = await session.execute(stmt)
        chunks = list(result.scalars().all())
        if chunks:
            self.clear()
            self.index_document_chunks(chunks)
            return len(chunks)
        return 0

    def search(
        self,
        query: str,
        top_k: int = settings.TOP_K_EVIDENCE,
        mode: str = "hybrid",
        alpha: float | None = None,
    ) -> list[dict]:
        """Search across indices and return raw ranked candidates."""
        return self.hybrid_retriever.retrieve(
            query=query,
            top_k=top_k,
            mode=mode,
            alpha=alpha,
        )

    def get_stats(self) -> dict:
        """Return operational telemetry about indexed chunks."""
        return {
            "total_vector_chunks": self.vector_retriever.get_total_indexed(),
            "total_sparse_chunks": self.sparse_retriever.get_total_indexed(),
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
            "rrf_k": settings.RRF_K,
            "default_alpha": settings.RRF_ALPHA,
        }

    def save(self, filepath_base: str | None = None) -> None:
        """Persist both FAISS and BM25 state."""
        self.save_indexes()

    def save_indexes(self) -> None:
        """Persist both FAISS and BM25 state."""
        try:
            self.vector_retriever.save(self.faiss_path)
            self.sparse_retriever.save(self.bm25_path)
        except Exception:
            pass

    def load_indexes(self) -> None:
        """Load FAISS and BM25 state from disk if available."""
        try:
            self.vector_retriever.load(self.faiss_path)
            self.sparse_retriever.load(self.bm25_path)
        except Exception:
            pass


# Global singleton instance
retrieval_engine = RetrievalEngine()
