import json
import os
from pathlib import Path
import numpy as np
import faiss
from backend.app.core.config import settings
from backend.app.models.document import DocumentChunk
from backend.app.services.retrieval.embeddings import embedding_provider
from backend.app.services.retrieval.interfaces import VectorRetrieverInterface


class FAISSRetriever(VectorRetrieverInterface):
    """FAISS-backed dense vector indexer implementing VectorRetrieverInterface."""

    def __init__(self, dimension: int = settings.EMBEDDING_DIMENSION):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Cosine similarity on normalized vectors
        self.chunk_ids: list[str] = []
        self._id_map: dict[str, int] = {}

    def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Embed and insert chunks into FAISS vector index."""
        if not chunks:
            return 0

        texts = [chunk.text_content for chunk in chunks]
        embeddings = embedding_provider.embed_documents(texts)
        vec_array = np.array(embeddings, dtype=np.float32)

        # Ensure L2-normalized
        faiss.normalize_L2(vec_array)

        start_idx = len(self.chunk_ids)
        self.index.add(vec_array)

        for i, chunk in enumerate(chunks):
            current_idx = start_idx + i
            self.chunk_ids.append(chunk.id)
            self._id_map[chunk.id] = current_idx
            chunk.embedding_id = current_idx

        return len(chunks)

    def search(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        """Search vector index. Returns list of (chunk_id, cosine_similarity)."""
        if self.index.ntotal == 0:
            return []

        q_vec = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(q_vec)

        actual_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(q_vec, actual_k)

        results: list[tuple[str, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.chunk_ids):
                chunk_id = self.chunk_ids[idx]
                # Clamp cosine similarity to [0.0, 1.0]
                normalized_score = max(0.0, min(1.0, float(score)))
                results.append((chunk_id, normalized_score))

        return results

    def get_total_indexed(self) -> int:
        return self.index.ntotal

    def save(self, filepath: str) -> None:
        """Persist FAISS binary index and chunk ID metadata."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path))

        meta_path = path.with_suffix(".json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"chunk_ids": self.chunk_ids, "dimension": self.dimension}, f)

    def load(self, filepath: str) -> bool:
        """Load FAISS binary index and metadata from disk."""
        path = Path(filepath)
        meta_path = path.with_suffix(".json")
        if not path.exists() or not meta_path.exists():
            return False

        try:
            self.index = faiss.read_index(str(path))
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.chunk_ids = data.get("chunk_ids", [])
                self._id_map = {cid: idx for idx, cid in enumerate(self.chunk_ids)}
            return True
        except Exception:
            return False
