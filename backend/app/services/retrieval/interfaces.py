from abc import ABC, abstractmethod
from typing import Any
from backend.app.models.document import DocumentChunk


class EmbeddingProviderInterface(ABC):
    """Abstract interface for dense semantic embedding providers."""

    @abstractmethod
    def get_dimension(self) -> int:
        """Return the vector dimensionality (e.g. 384)."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate a dense embedding vector for a single string query."""
        pass

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate dense embedding vectors for a batch of document texts."""
        pass


class VectorRetrieverInterface(ABC):
    """Abstract interface for dense vector indexers (e.g. FAISS, Qdrant)."""

    @abstractmethod
    def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Add document chunks to the vector index. Returns number of indexed chunks."""
        pass

    @abstractmethod
    def search(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        """Search vector index. Returns list of (chunk_id, cosine_similarity_score)."""
        pass

    @abstractmethod
    def get_total_indexed(self) -> int:
        """Return total number of chunks currently in the vector index."""
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        """Persist index state to disk."""
        pass

    @abstractmethod
    def load(self, filepath: str) -> bool:
        """Load index state from disk."""
        pass


class SparseRetrieverInterface(ABC):
    """Abstract interface for sparse keyword indexers (e.g. BM25Okapi)."""

    @abstractmethod
    def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Add document chunks to the sparse term index. Returns count."""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Search sparse index. Returns list of (chunk_id, normalized_bm25_score)."""
        pass

    @abstractmethod
    def get_total_indexed(self) -> int:
        """Return total number of chunks currently in the sparse index."""
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        """Persist index state to disk."""
        pass

    @abstractmethod
    def load(self, filepath: str) -> bool:
        """Load index state from disk."""
        pass
