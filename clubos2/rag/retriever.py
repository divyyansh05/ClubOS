"""Hybrid retrieval pipeline for ClubOS 2.0.

Retrieval order:
1. Embed query → vector search ChromaDB (k_vector results)
2. BM25 keyword search over all chunks in memory (k_bm25 results)
3. Merge candidates via Reciprocal Rank Fusion (RRF)
4. If use_reranker: cross-encoder rerank → return top k_final
   Else: linear-combine vector + BM25 scores → return top k_final

All chunks returned carry a populated `source` and `section` for citation.
"""

from __future__ import annotations

import logging
import os
import string
from typing import TYPE_CHECKING, Any

import chromadb
from pydantic import BaseModel

from clubos2.observability.tracing import traced
from clubos2.rag.embeddings import embed_texts
from clubos2.tools.registry import KnowledgeChunk

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder

logger = logging.getLogger("clubos.rag.retriever")

# ---------------------------------------------------------------------------
# Lazy-loaded cross-encoder (downloaded once, cached by sentence-transformers)
# ---------------------------------------------------------------------------
_RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_reranker: CrossEncoder | None = None


def _get_reranker() -> CrossEncoder:
    """Lazy-load the cross-encoder on first use (~80 MB, cached by HuggingFace)."""
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder  # noqa: PLC0415

        logger.info("Loading cross-encoder reranker model '%s' ...", _RERANKER_MODEL_NAME)
        _reranker = CrossEncoder(_RERANKER_MODEL_NAME)
        logger.info("Cross-encoder reranker loaded.")
    return _reranker


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class RetrievalConfig(BaseModel):
    k_vector: int = 20  # results pulled from vector search
    k_bm25: int = 20  # results pulled from BM25 search
    k_final: int = 5  # results returned after reranking
    use_reranker: bool = True
    vector_weight: float = 0.6  # used only when use_reranker=False
    bm25_weight: float = 0.4  # used only when use_reranker=False


# ---------------------------------------------------------------------------
# BM25 helpers
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text.split()


def _bm25_search(
    query: str,
    corpus_ids: list[str],
    corpus_texts: list[str],
    k: int,
) -> list[tuple[str, float]]:
    """Run BM25Okapi over corpus_texts, return top-k (chunk_id, score) pairs.

    # OPTIMIZATION: cache BM25 index, invalidate on ingest.
    """
    from rank_bm25 import BM25Okapi  # noqa: PLC0415  # type: ignore[import-untyped]

    tokenized_corpus = [_tokenize(t) for t in corpus_texts]
    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_query = _tokenize(query)
    scores: list[float] = bm25.get_scores(tokenized_query).tolist()

    ranked = sorted(
        zip(corpus_ids, scores, strict=False),
        key=lambda x: x[1],
        reverse=True,
    )
    return [(cid, score) for cid, score in ranked[:k] if score > 0]


# ---------------------------------------------------------------------------
# RRF fusion
# ---------------------------------------------------------------------------

_RRF_K = 60  # standard RRF constant


def _rrf_fuse(
    vector_ranked: list[str],
    bm25_ranked: list[str],
) -> dict[str, float]:
    """Reciprocal Rank Fusion over two ranked lists of chunk IDs."""
    rrf_scores: dict[str, float] = {}

    for rank, cid in enumerate(vector_ranked, start=1):
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (_RRF_K + rank)

    for rank, cid in enumerate(bm25_ranked, start=1):
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (_RRF_K + rank)

    return rrf_scores


# ---------------------------------------------------------------------------
# Main retrieve function
# ---------------------------------------------------------------------------


@traced(name="rag:retrieve", run_type="retriever")
async def retrieve(
    query: str,
    retrieval_config: RetrievalConfig | None = None,
    metadata_filter: dict[str, Any] | None = None,
) -> list[KnowledgeChunk]:
    """Hybrid retrieval: vector search + BM25 + optional cross-encoder reranking.

    Args:
        query: Natural language query from the Scout agent.
        retrieval_config: Retrieval hyperparameters. Uses defaults if None.
            NOTE: deliberately NOT named 'config' to avoid collision with
            LangSmith/LangChain's convention that intercepts a second positional
            argument named 'config' as a runnable config dict.
        metadata_filter: Optional ChromaDB `where` dict to restrict to a
            specific source file, e.g. ``{"source": "signal_engine.md"}``.

    Returns:
        Up to ``retrieval_config.k_final`` KnowledgeChunk objects, sorted by relevance.
        Returns [] if no relevant chunks are found (not an error).
    """
    if retrieval_config is None:
        retrieval_config = RetrievalConfig()
    config = retrieval_config

    persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "./var/chroma")

    # ------------------------------------------------------------------
    # 1. Connect to ChromaDB
    # ------------------------------------------------------------------
    try:
        chroma_client = chromadb.PersistentClient(path=persist_dir)
        collection = chroma_client.get_collection("clubos_skills")
    except Exception as exc:
        logger.error("Failed to connect to ChromaDB collection 'clubos_skills': %s", exc)
        return []

    total_chunks = collection.count()
    if total_chunks == 0:
        logger.warning("ChromaDB 'clubos_skills' collection is empty — run ingest first.")
        return []

    # ------------------------------------------------------------------
    # 2. Embed query & vector search
    # ------------------------------------------------------------------
    query_vectors = await embed_texts([query])
    query_vector = query_vectors[0]

    vector_where = metadata_filter if metadata_filter else None
    vector_n = min(config.k_vector, total_chunks)

    vector_results: Any
    try:
        vector_results = collection.query(
            query_embeddings=[query_vector],  # type: ignore[arg-type]  # ChromaDB stub
            n_results=vector_n,
            where=vector_where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as exc:
        logger.error("Vector search failed: %s", exc)
        vector_results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    raw_ids: list[str] = vector_results["ids"][0]
    raw_docs: list[str] = vector_results["documents"][0]
    raw_metas: list[dict[str, Any]] = vector_results["metadatas"][0]
    raw_distances: list[float] = vector_results["distances"][0]

    # Map chunk_id → (text, metadata, cosine_similarity)
    id_to_text: dict[str, str] = {}
    id_to_meta: dict[str, dict[str, Any]] = {}
    id_to_vector_score: dict[str, float] = {}

    for cid, doc, meta, dist in zip(raw_ids, raw_docs, raw_metas, raw_distances, strict=False):
        id_to_text[cid] = doc
        id_to_meta[cid] = meta or {}
        # ChromaDB cosine distance → similarity: similarity = 1 - distance
        id_to_vector_score[cid] = max(0.0, 1.0 - dist)

    # ------------------------------------------------------------------
    # 3. Load all chunks for BM25 (small corpus in Phase 1)
    # ------------------------------------------------------------------
    all_chunks_result: Any
    try:
        all_chunks_result = collection.get(
            where=vector_where,
            include=["documents", "metadatas"],
        )
        bm25_ids: list[str] = list(all_chunks_result.get("ids") or [])
        bm25_docs: list[str] = list(all_chunks_result.get("documents") or [])
        bm25_metas: list[dict[str, Any]] = list(all_chunks_result.get("metadatas") or [])
    except Exception as exc:
        logger.error("Failed to load corpus for BM25: %s", exc)
        bm25_ids, bm25_docs, bm25_metas = [], [], []

    # Merge any BM25 chunk info not already in id_to_text
    for cid, doc, meta in zip(bm25_ids, bm25_docs, bm25_metas, strict=False):
        if cid not in id_to_text:
            id_to_text[cid] = doc
            id_to_meta[cid] = meta or {}

    bm25_ranked_pairs = _bm25_search(
        query=query,
        corpus_ids=bm25_ids,
        corpus_texts=bm25_docs,
        k=config.k_bm25,
    )
    id_to_bm25_score: dict[str, float] = {cid: score for cid, score in bm25_ranked_pairs}
    bm25_ranked_ids = [cid for cid, _ in bm25_ranked_pairs]

    # ------------------------------------------------------------------
    # 4. RRF fusion — merge vector + BM25 ranked lists
    # ------------------------------------------------------------------
    rrf_scores = _rrf_fuse(
        vector_ranked=raw_ids,
        bm25_ranked=bm25_ranked_ids,
    )

    # Determine candidate pool for reranking
    candidate_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)
    # Take enough candidates for reranker but not too many
    candidates_for_rerank = candidate_ids[: max(config.k_final * 4, 20)]

    # ------------------------------------------------------------------
    # 5a. Reranker path
    # ------------------------------------------------------------------
    if config.use_reranker and candidates_for_rerank:
        try:
            reranker = _get_reranker()

            @traced(name="reranker", run_type="chain")
            async def _rerank(pairs: list[tuple[str, str]]) -> list[float]:
                scores: list[float] = reranker.predict(pairs).tolist()  # type: ignore[arg-type]
                return scores

            query_doc_pairs = [
                (query, id_to_text[cid]) for cid in candidates_for_rerank if cid in id_to_text
            ]
            valid_ids = [cid for cid in candidates_for_rerank if cid in id_to_text]

            rerank_scores: list[float] = await _rerank(query_doc_pairs)

            scored = sorted(
                zip(valid_ids, rerank_scores, strict=False),
                key=lambda x: x[1],
                reverse=True,
            )
            final_ids = [cid for cid, _ in scored[: config.k_final]]
            final_scores_map = {cid: score for cid, score in scored}

        except Exception as exc:
            logger.warning("Reranker failed (%s) — falling back to RRF scores.", exc)
            final_ids = candidates_for_rerank[: config.k_final]
            final_scores_map = rrf_scores

    # ------------------------------------------------------------------
    # 5b. Linear-combine fallback (use_reranker=False or reranker error)
    # ------------------------------------------------------------------
    else:
        all_candidate_ids = set(raw_ids) | set(bm25_ranked_ids)

        # Normalise BM25 scores to [0,1] for fair weighting
        max_bm25 = max(id_to_bm25_score.values(), default=1.0) or 1.0
        normalised_bm25 = {cid: s / max_bm25 for cid, s in id_to_bm25_score.items()}

        combined: dict[str, float] = {}
        for cid in all_candidate_ids:
            v_score = id_to_vector_score.get(cid, 0.0) * config.vector_weight
            b_score = normalised_bm25.get(cid, 0.0) * config.bm25_weight
            combined[cid] = v_score + b_score

        sorted_combined = sorted(combined, key=lambda x: combined[x], reverse=True)
        final_ids = sorted_combined[: config.k_final]
        final_scores_map = combined

    # ------------------------------------------------------------------
    # 6. Build KnowledgeChunk results — citation guarantee: source + section
    # ------------------------------------------------------------------
    results: list[KnowledgeChunk] = []
    for cid in final_ids:
        text = id_to_text.get(cid, "")
        meta = id_to_meta.get(cid, {})
        score = float(final_scores_map.get(cid, 0.0))

        source = str(meta.get("source", "unknown"))
        section = str(meta.get("section", "unknown"))

        if not text:
            logger.warning("Chunk %s has empty text — skipping.", cid)
            continue

        results.append(
            KnowledgeChunk(
                text=text,
                source=source,
                section=section,
                score=score,
            )
        )

    logger.info(
        "retrieve('%s'): vector=%d BM25=%d candidates=%d final=%d",
        query[:60],
        len(raw_ids),
        len(bm25_ranked_ids),
        len(candidates_for_rerank),
        len(results),
    )
    return results
