"""Tests for the real search_knowledge tool (Prompt 3.4).

Tests use:
- An isolated ChromaDB in tmp_path populated with representative chunks.
- Mocked OpenAI embeddings (no real API calls).
- The real retriever pipeline (BM25 + vector + mocked cross-encoder).
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import chromadb
import pytest

from clubos2.tools.registry import KnowledgeChunk, search_knowledge

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_embed():
    """Mock embed_texts to return deterministic dummy vectors."""

    async def _embed(texts: list[str]) -> list[list[float]]:
        return [[0.1 + 0.01 * i] * 1536 for i, _ in enumerate(texts)]

    with patch("clubos2.rag.retriever.embed_texts", new_callable=AsyncMock) as m:
        m.side_effect = _embed
        yield m


@pytest.fixture()
def mock_reranker():
    """Mock cross-encoder — scores 'seasonal' content higher."""
    import numpy as np

    mock_model = MagicMock()

    def fake_predict(pairs):
        scores = []
        for _q, doc in pairs:
            if any(word in doc.lower() for word in ("seasonal", "january", "z-score")):
                scores.append(5.0)
            elif "signal" in doc.lower():
                scores.append(3.0)
            else:
                scores.append(1.0)
        return np.array(scores)

    mock_model.predict = fake_predict
    with patch("clubos2.rag.retriever._get_reranker", return_value=mock_model):
        yield mock_model


@pytest.fixture()
def populated_chroma(tmp_path, mock_embed):
    """Isolated ChromaDB collection with representative skill chunks."""
    chroma_dir = tmp_path / "chroma"
    os.makedirs(chroma_dir, exist_ok=True)

    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_or_create_collection("clubos_skills", metadata={"hnsw:space": "cosine"})

    chunks = [
        {
            "id": "pb_gotchas",
            "text": (
                "January net_sales always drops 12-18% post-holiday. "
                "The seasonal Z-score corrects for historical monthly patterns."
            ),
            "source": "priority_board.md",
            "section": "Known gotchas",
        },
        {
            "id": "pb_purpose",
            "text": "The Priority Board answers: which metrics need attention this month?",
            "source": "priority_board.md",
            "section": "Purpose",
        },
        {
            "id": "se_validation",
            "text": (
                "Signal validation requires: Pearson r >= 0.60, "
                "temporal lag 1-3 months, commercial logic review."
            ),
            "source": "signal_engine.md",
            "section": "Known gotchas",
        },
    ]

    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=[[0.1] * 1536 for _ in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["source"], "section": c["section"]} for c in chunks],
    )

    return chroma_dir, collection


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_knowledge_returns_chunks_with_populated_source(
    populated_chroma, mock_embed, mock_reranker
):
    """Every returned KnowledgeChunk must have a populated source and section."""
    chroma_dir, _ = populated_chroma

    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}):
        results = await search_knowledge("seasonal patterns January")

    assert len(results) > 0
    for chunk in results:
        assert isinstance(chunk, KnowledgeChunk)
        assert chunk.source, "source must not be empty"
        assert chunk.section, "section must not be empty"
        assert chunk.text, "text must not be empty"


@pytest.mark.asyncio
async def test_search_knowledge_seasonal_query_cites_priority_board(
    populated_chroma, mock_embed, mock_reranker
):
    """Seasonal Z-score query should surface priority_board.md."""
    chroma_dir, _ = populated_chroma

    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}):
        results = await search_knowledge("seasonal Z-score January")

    sources = [r.source for r in results]
    assert "priority_board.md" in sources, f"Expected priority_board.md in sources, got: {sources}"


@pytest.mark.asyncio
async def test_search_knowledge_respects_k_limit(populated_chroma, mock_embed, mock_reranker):
    """search_knowledge(k=2) must return at most 2 chunks."""
    chroma_dir, _ = populated_chroma

    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}):
        results = await search_knowledge("seasonal Z-score", k=2)

    assert len(results) <= 2, f"Expected at most 2 chunks, got {len(results)}"


@pytest.mark.asyncio
async def test_search_knowledge_empty_corpus_returns_empty(tmp_path, mock_embed):
    """Empty ChromaDB collection should return [] without error."""
    chroma_dir = tmp_path / "empty_chroma"
    os.makedirs(chroma_dir, exist_ok=True)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    client.get_or_create_collection("clubos_skills", metadata={"hnsw:space": "cosine"})

    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}):
        results = await search_knowledge("seasonal patterns")

    assert results == []


@pytest.mark.asyncio
async def test_search_knowledge_chunks_never_have_unknown_source(
    populated_chroma, mock_embed, mock_reranker
):
    """Citation guarantee: source must never be 'unknown'."""
    chroma_dir, _ = populated_chroma

    with patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}):
        results = await search_knowledge("priority board signal validation")

    for chunk in results:
        assert (
            chunk.source != "unknown"
        ), f"source must never be 'unknown', got chunk from section: {chunk.section}"
        assert (
            chunk.section != "unknown"
        ), f"section must never be 'unknown', got chunk from source: {chunk.source}"
