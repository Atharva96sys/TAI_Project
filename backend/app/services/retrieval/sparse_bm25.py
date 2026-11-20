import json
import math
import re
from pathlib import Path
from rank_bm25 import BM25Okapi
from backend.app.models.document import DocumentChunk
from backend.app.services.retrieval.interfaces import SparseRetrieverInterface

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
    "i", "if", "in", "into", "is", "isn't", "it", "its", "itself", "just", "me", "more", "most", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "our", "ours", "ourselves",
    "out", "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "wasn't", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}


class BM25Retriever(SparseRetrieverInterface):
    """BM25Okapi keyword search implementation for exact terminology and dosage retrieval."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunk_ids: list[str] = []
        self.corpus_tokens: list[list[str]] = []
        self.bm25: BM25Okapi | None = None

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """Tokenize text into lowercase alphanumeric tokens with stopword filtering."""
        tokens = re.findall(r"\b[a-zA-Z0-9\.\-\/]+\b", text.lower())
        return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

    def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Tokenize and add chunks to the BM25 index."""
        if not chunks:
            return 0

        for chunk in chunks:
            self.chunk_ids.append(chunk.id)
            tokens = self.tokenize(chunk.text_content)
            self.corpus_tokens.append(tokens)

        # Re-initialize BM25 with updated corpus
        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens, k1=self.k1, b=self.b)

        return len(chunks)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Search BM25 term index. Returns list of (chunk_id, normalized_score)."""
        if not self.chunk_ids or not self.corpus_tokens:
            return []

        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        q_set = set(query_tokens)
        scored_candidates: list[tuple[str, float]] = []

        # If BM25 is available, compute scores
        raw_scores = self.bm25.get_scores(query_tokens) if self.bm25 else [0.0] * len(self.chunk_ids)
        max_score = float(max(raw_scores)) if len(raw_scores) > 0 else 0.0

        for idx, (cid, doc_tokens) in enumerate(zip(self.chunk_ids, self.corpus_tokens)):
            doc_set = set(doc_tokens)
            overlap = len(q_set.intersection(doc_set))
            if overlap == 0:
                continue

            # If BM25 raw score is positive and normalized
            if max_score > 0.0 and raw_scores[idx] > 0.0:
                score = min(1.0, float(raw_scores[idx] / max_score))
            else:
                # Term overlap ratio for single/small doc collections
                score = min(1.0, float(overlap / len(q_set)))

            scored_candidates.append((cid, round(score, 4)))

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates[:top_k]

    def get_total_indexed(self) -> int:
        return len(self.chunk_ids)

    def save(self, filepath: str) -> None:
        """Persist BM25 state to JSON."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "chunk_ids": self.chunk_ids,
            "corpus_tokens": self.corpus_tokens,
            "k1": self.k1,
            "b": self.b,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load(self, filepath: str) -> bool:
        """Load BM25 state from JSON."""
        path = Path(filepath)
        if not path.exists():
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.chunk_ids = data.get("chunk_ids", [])
                self.corpus_tokens = data.get("corpus_tokens", [])
                self.k1 = data.get("k1", 1.5)
                self.b = data.get("b", 0.75)
                if self.corpus_tokens:
                    self.bm25 = BM25Okapi(self.corpus_tokens, k1=self.k1, b=self.b)
            return True
        except Exception:
            return False
