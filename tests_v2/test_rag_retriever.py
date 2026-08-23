"""Tests for the hybrid retrieval pipeline (clubos2/rag/retriever.py).

Strategy
--------
- All OpenAI embedding calls are mocked to return deterministic dummy vectors.
- ChromaDB is pointed at a pytest tmp_path directory so tests are isolated.
- The cross-encoder reranker is mocked to avoid downloading ~80 MB models in CI.
- The BM25 path is tested with use_reranker=False.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import chromadb
import pytest

from clubos2.rag.retriever import (
    RetrievalConfig,
    _bm25_search,
    _rrf_fuse,
    _tokenize,
    retrieve,
)
from clubos2.tools.registry import KnowledgeChunk

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_embed():
    """Mock embed_texts to return dummy 1536-dim vectors."""

    async def _embed(texts: list[str]) -> list[list[float]]:
        # Each unique text gets a slightly different vector so retrieval is non-trivial
        return [[float(i % 10) * 0.1 + 0.01 * len(t)] * 1536 for i, t in enumerate(texts)]

    with patch("clubos2.rag.retriever.embed_texts", new_callable=AsyncMock) as m:
        m.side_effect = _embed
        yield m


@pytest.fixture()
def mock_reranker():
    """Mock the cross-encoder to avoid downloading 80 MB model."""
    mock_model = MagicMock()

    # Score higher for pairs that contain the word 'seasonal' or 'January'
    def fake_predict(pairs: list[tuple[str, str]]) -> list[float]:
        import numpy as np  # noqa: PLC0415

        scores = []
        for _query, doc in pairs:
            if "seasonal" in doc.lower() or "january" in doc.lower():
                scores.append(5.0)
            elif "signal" in doc.lower() or "correlation" in doc.lower():
                scores.append(3.0)
            else:
                scores.append(1.0)
        return np.array(scores)

    mock_model.predict = fake_predict

    with patch("clubos2.rag.retriever._get_reranker", return_value=mock_model):
        yield mock_model


@pytest.fixture()
def populated_chroma(tmp_path, mock_embed):
    """Create and populate an isolated ChromaDB with sample skill chunks."""
    chroma_dir = tmp_path / "chroma"
    os.makedirs(chroma_dir, exist_ok=True)

    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection(
        name="clubos_skills", metadata={"hnsw:space": "cosine"}
    )

    # Seed representative chunks that mimic real skill files
    chunks = [
        {
            "id": "chunk_pb_gotchas",
            "text": (
                "January net_sales always drops 12-18% post-holiday. "
                "The seasonal Z-score scoring corrects for this historical monthly pattern. "
                "If you see net_sales rank #1 in January, check whether "
                "the rolling-average bug has returned."
            ),
            "source": "priority_board.md",
            "section": "Known gotchas",
        },
        {
            "id": "chunk_pb_purpose",
            "text": (
                "The Priority Board is the hero screen of ClubOS. It answers: "
                "'Which metrics need attention this month?' using a 5-component scoring formula."
            ),
            "source": "priority_board.md",
            "section": "Purpose",
        },
        {
            "id": "chunk_se_validation",
            "text": (
                "Signal validation requires three gates: statistical strength (Pearson r >= 0.60), "
                "commercial logic review, and temporal precedence (1-3 month lag). "
                "The unique_visitors -> net_sales signal shows a 2-month lag with 69% correlation."
            ),
            "source": "signal_engine.md",
            "section": "Known gotchas",
        },
        {
            "id": "chunk_se_purpose",
            "text": (
                "The Signal Engine identifies leading indicators — metrics that predict future "
                "commercial outcomes 1-3 months in advance."
            ),
            "source": "signal_engine.md",
            "section": "Purpose",
        },
        {
            "id": "chunk_pb_scoring",
            "text": (
                "The 5-component priority scoring weights are fixed: "
                "30/25/20/15/10. Do not renormalise these weights per-question."
            ),
            "source": "priority_board.md",
            "section": "Known gotchas",
        },
    ]

    # Use dummy embeddings (1536 dims)
    dummy_embeddings = [[0.1] * 1536 for _ in chunks]

    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=dummy_embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["source"], "section": c["section"]} for c in chunks],
    )

    return chroma_dir, collection


# ---------------------------------------------------------------------------
# Unit tests — BM25 helpers
# ---------------------------------------------------------------------------


def test_tokenize_lowercases_and_removes_punctuation():
    tokens = _tokenize("Hello, World! It's great.")
    assert "hello" in tokens
    assert "world" in tokens
    # Punctuation removed — 'It's' becomes 'its'
    assert all(c not in string.punctuation for token in tokens for c in token)


def test_bm25_search_returns_relevant_chunk():
    corpus_ids = ["a", "b", "c"]
    corpus_texts = [
        "seasonal Z-score January correction",
        "recipe for pasta carbonara",
        "signal correlation lag months",
    ]
    results = _bm25_search("seasonal January", corpus_ids, corpus_texts, k=3)
    result_ids = [r[0] for r in results]
    assert "a" in result_ids
    assert result_ids[0] == "a", "Most relevant chunk should rank first"


def test_bm25_search_excludes_zero_score():
    corpus_ids = ["a", "b"]
    corpus_texts = ["something completely unrelated", "another unrelated text"]
    results = _bm25_search("seasonal January Z-score", corpus_ids, corpus_texts, k=2)
    # All scores are 0 — should return empty
    assert results == []


def test_rrf_fuse_boosts_shared_chunks():
    vector_ranked = ["chunk_a", "chunk_b", "chunk_c"]
    bm25_ranked = ["chunk_c", "chunk_a", "chunk_d"]
    rrf = _rrf_fuse(vector_ranked, bm25_ranked)

    # chunk_a appears in both lists → should outscore chunk_d (only in BM25)
    assert rrf["chunk_a"] > rrf["chunk_d"]
    # chunk_c appears in both lists → should outscore chunk_b (only in vector)
    assert rrf["chunk_c"] > rrf["chunk_b"]


# ---------------------------------------------------------------------------
# Integration tests — retrieve()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retrieve_empty_collection_returns_empty(tmp_path, mock_embed):
    """Empty collection → should return [] without error."""
    chroma_dir = tmp_path / "empty_chroma"
    os.makedirs(chroma_dir, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    client.get_or_create_collection("clubos_skills", metadata={"hnsw:space": "cosine"})

    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}):
        results = await retrieve("what is the seasonal Z-score?")

    assert results == []


@pytest.mark.asyncio
async def test_retrieve_returns_knowledge_chunks(populated_chroma, mock_embed, mock_reranker):
    """Retrieval returns typed KnowledgeChunk objects with populated source + section."""
    chroma_dir, _ = populated_chroma
    config = RetrievalConfig(k_vector=5, k_bm25=5, k_final=3, use_reranker=True)

    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}):
        results = await retrieve("seasonal Z-score January", retrieval_config=config)

    assert len(results) > 0
    assert len(results) <= 3

    for chunk in results:
        assert isinstance(chunk, KnowledgeChunk)
        assert chunk.source != "unknown", "source must always be populated"
        assert chunk.section != "unknown", "section must always be populated"
        assert len(chunk.text) > 0


@pytest.mark.asyncio
async def test_retrieve_seasonal_query_returns_priority_board(
    populated_chroma, mock_embed, mock_reranker
):
    """A query about January seasonal patterns should surface priority_board.md."""
    chroma_dir, _ = populated_chroma
    config = RetrievalConfig(k_vector=5, k_bm25=5, k_final=3, use_reranker=True)

    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}):
        results = await retrieve(
            "what does the seasonal Z-score correct for in January?", retrieval_config=config
        )

    assert len(results) > 0
    sources = [r.source for r in results]
    assert "priority_board.md" in sources, f"Expected priority_board.md in results, got: {sources}"


@pytest.mark.asyncio
async def test_retrieve_metadata_filter_restricts_source(
    populated_chroma, mock_embed, mock_reranker
):
    """metadata_filter={'source': 'signal_engine.md'} should only return signal_engine chunks."""
    chroma_dir, _ = populated_chroma
    config = RetrievalConfig(k_vector=5, k_bm25=5, k_final=5, use_reranker=True)

    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}):
        results = await retrieve(
            "signal correlation lag months",
            retrieval_config=config,
            metadata_filter={"source": "signal_engine.md"},
        )

    assert len(results) > 0
    for chunk in results:
        assert chunk.source == "signal_engine.md", f"Filter failed — got chunk from: {chunk.source}"


@pytest.mark.asyncio
async def test_retrieve_without_reranker_still_works(populated_chroma, mock_embed):
    """use_reranker=False falls back to linear-combine — no cross-encoder needed."""
    chroma_dir, _ = populated_chroma
    config = RetrievalConfig(k_vector=5, k_bm25=5, k_final=3, use_reranker=False)

    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}):
        results = await retrieve("seasonal Z-score January", retrieval_config=config)

    assert len(results) > 0
    for chunk in results:
        assert chunk.source != "unknown"
        assert chunk.section != "unknown"


@pytest.mark.asyncio
async def test_retrieve_all_chunks_have_source_and_section(
    populated_chroma, mock_embed, mock_reranker
):
    """Citation guarantee: every returned chunk must have non-empty source and section."""
    chroma_dir, _ = populated_chroma
    config = RetrievalConfig(k_vector=5, k_bm25=5, k_final=5, use_reranker=True)

    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}):
        results = await retrieve("priority board scoring weights", retrieval_config=config)

    for chunk in results:
        assert chunk.source, "source must not be empty"
        assert chunk.section, "section must not be empty"
        assert chunk.text, "text must not be empty"


# Required for string.punctuation reference in test
import string  # noqa: E402
