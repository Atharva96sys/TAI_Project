from typing import Any
from backend.app.core.config import settings
from backend.app.services.retrieval.dense_faiss import FAISSRetriever
from backend.app.services.retrieval.embeddings import embedding_provider
from backend.app.services.retrieval.sparse_bm25 import BM25Retriever


class HybridRetriever:
    """Combines Dense Vector (FAISS) and Sparse Keyword (BM25) search using Reciprocal Rank Fusion."""

    def __init__(
        self,
        vector_retriever: FAISSRetriever,
        sparse_retriever: BM25Retriever,
        rrf_k: int = settings.RRF_K,
        default_alpha: float = settings.RRF_ALPHA,
    ):
        self.vector_retriever = vector_retriever
        self.sparse_retriever = sparse_retriever
        self.rrf_k = rrf_k
        self.default_alpha = default_alpha

    def retrieve(
        self,
        query: str,
        top_k: int = settings.TOP_K_EVIDENCE,
        top_n_candidates: int = settings.TOP_N_CANDIDATES,
        mode: str = "hybrid",
        alpha: float | None = None,
    ) -> list[dict[str, Any]]:
        """Execute search in 'hybrid', 'dense', or 'sparse' mode and compute fused scores."""
        alpha_val = alpha if alpha is not None else self.default_alpha

        dense_results: list[tuple[str, float]] = []
        sparse_results: list[tuple[str, float]] = []

        # 1. Dense retrieval
        if mode in ["hybrid", "dense"]:
            query_vector = embedding_provider.embed_text(query)
            dense_results = self.vector_retriever.search(query_vector, top_k=top_n_candidates)

        # 2. Sparse retrieval
        if mode in ["hybrid", "sparse"]:
            sparse_results = self.sparse_retriever.search(query, top_k=top_n_candidates)

        # 3. Dense-only mode
        if mode == "dense":
            output = []
            for rank, (cid, score) in enumerate(dense_results[:top_k], start=1):
                output.append({
                    "chunk_id": cid,
                    "dense_score": float(score),
                    "sparse_score": 0.0,
                    "rrf_score": float(score),
                    "rerank_score": float(score),
                    "rank_position": rank,
                })
            return output

        # 4. Sparse-only mode
        if mode == "sparse":
            output = []
            for rank, (cid, score) in enumerate(sparse_results[:top_k], start=1):
                output.append({
                    "chunk_id": cid,
                    "dense_score": 0.0,
                    "sparse_score": float(score),
                    "rrf_score": float(score),
                    "rerank_score": float(score),
                    "rank_position": rank,
                })
            return output

        # 5. Hybrid Reciprocal Rank Fusion (RRF)
        # Build rank maps
        dense_rank_map = {cid: rank for rank, (cid, _) in enumerate(dense_results, start=1)}
        dense_score_map = {cid: score for cid, score in dense_results}

        sparse_rank_map = {cid: rank for rank, (cid, _) in enumerate(sparse_results, start=1)}
        sparse_score_map = {cid: score for cid, score in sparse_results}

        all_chunk_ids = set(dense_rank_map.keys()).union(set(sparse_rank_map.keys()))
        if not all_chunk_ids:
            return []

        fused_candidates: list[dict[str, Any]] = []

        for cid in all_chunk_ids:
            d_rank = dense_rank_map.get(cid)
            s_rank = sparse_rank_map.get(cid)

            # RRF Formula: alpha / (k + rank_dense) + (1 - alpha) / (k + rank_sparse)
            dense_rrf = (alpha_val / (self.rrf_k + d_rank)) if d_rank is not None else 0.0
            sparse_rrf = ((1.0 - alpha_val) / (self.rrf_k + s_rank)) if s_rank is not None else 0.0
            rrf_score = dense_rrf + sparse_rrf

            d_score = dense_score_map.get(cid, 0.0)
            s_score = sparse_score_map.get(cid, 0.0)

            # Normalized Rerank approximation based on balanced hybrid score
            combined_raw = (alpha_val * d_score) + ((1.0 - alpha_val) * s_score)

            fused_candidates.append({
                "chunk_id": cid,
                "dense_score": round(d_score, 4),
                "sparse_score": round(s_score, 4),
                "rrf_score": round(rrf_score, 6),
                "rerank_score": round(combined_raw, 4),
            })

        # Sort by RRF score descending
        fused_candidates.sort(key=lambda x: x["rrf_score"], reverse=True)

        # Slice top_k and assign 1-indexed rank position
        top_evidence = fused_candidates[:top_k]
        for rank, item in enumerate(top_evidence, start=1):
            item["rank_position"] = rank

        return top_evidence
