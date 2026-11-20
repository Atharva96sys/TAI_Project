from backend.app.services.retrieval.interfaces import (
    EmbeddingProviderInterface,
    VectorRetrieverInterface,
    SparseRetrieverInterface,
)
from backend.app.services.retrieval.embeddings import embedding_provider, LocalEmbeddingProvider
from backend.app.services.retrieval.dense_faiss import FAISSRetriever
from backend.app.services.retrieval.sparse_bm25 import BM25Retriever
from backend.app.services.retrieval.hybrid_rrf import HybridRetriever
from backend.app.services.retrieval.provenance import ProvenanceResolver
from backend.app.services.retrieval.engine import retrieval_engine, RetrievalEngine

__all__ = [
    "EmbeddingProviderInterface",
    "VectorRetrieverInterface",
    "SparseRetrieverInterface",
    "embedding_provider",
    "LocalEmbeddingProvider",
    "FAISSRetriever",
    "BM25Retriever",
    "HybridRetriever",
    "ProvenanceResolver",
    "retrieval_engine",
    "RetrievalEngine",
]
