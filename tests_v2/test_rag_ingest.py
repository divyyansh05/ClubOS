from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from clubos2.rag.chunker import chunk_markdown_by_section
from clubos2.rag.ingest import ingest_skills


@pytest.fixture
def mock_embed_texts():
    """Fixture to mock embed_texts returning dummy 1536-dimensional vectors."""

    async def mock_embed(texts):
        return [[0.1] * 1536 for _ in texts]

    with patch("clubos2.rag.ingest.embed_texts", new_callable=AsyncMock) as mock:
        mock.side_effect = mock_embed
        yield mock


def test_chunk_markdown_by_section(tmp_path):
    """Verify chunk_markdown_by_section splits a test markdown correctly into chunks."""
    md_content = (
        "# Test Screen\n\n"
        "## Purpose\n"
        "This is the purpose paragraph.\n\n"
        "## Metrics on this screen\n"
        "- metric_one\n"
        "- metric_two\n\n"
        "## Valid queries\n"
        "What is the first query?\n"
    )
    test_file = tmp_path / "test_screen.md"
    test_file.write_text(md_content, encoding="utf-8")

    chunks = chunk_markdown_by_section(str(test_file))

    assert len(chunks) == 3

    # Verify metadata and sections
    assert chunks[0].section == "Purpose"
    assert "purpose paragraph" in chunks[0].text
    assert chunks[0].metadata["source"] == "skills.test_screen"
    assert chunks[0].metadata["section"] == "Purpose"

    assert chunks[1].section == "Metrics on this screen"
    assert "metric_one" in chunks[1].text

    assert chunks[2].section == "Valid queries"
    assert "first query" in chunks[2].text

    # Verify stable IDs
    assert chunks[0].chunk_id != chunks[1].chunk_id


@pytest.mark.asyncio
async def test_ingest_skills_lifecycle(tmp_path, mock_embed_texts):
    """Verify that ingest_skills runs, is idempotent, and drops/rebuilds on force_rebuild."""
    # We patch the CHROMA_PERSIST_DIR env var to write to a temp directory
    chroma_dir = tmp_path / "chroma"
    skills_dir = tmp_path / "skills"
    os.makedirs(skills_dir, exist_ok=True)

    # Write a mock skill file to our temp skills directory
    mock_skill = (
        "# Mock Board\n\n"
        "## Purpose\n"
        "Mock Board screen purpose.\n\n"
        "## Metrics on this screen\n"
        "- mock_metric\n\n"
        "## Valid queries\n"
        "Mock query?\n\n"
        "## Invalid queries\n"
        "Mock invalid query?\n\n"
        "## Known gotchas\n"
        "Gotcha detail.\n\n"
        "## Stakeholder language\n"
        "Terminology detail.\n\n"
        "## What the Scout should NEVER do with this screen\n"
        "Never do this.\n\n"
        "## References\n"
        "Reference detail.\n"
    )
    test_file = skills_dir / "mock_board.md"
    test_file.write_text(mock_skill, encoding="utf-8")

    # Patch environment and local directories in ingest
    with (
        patch.dict(os.environ, {"CHROMA_PERSIST_DIR": str(chroma_dir)}),
        patch("clubos2.rag.ingest.os.path.dirname", return_value=str(tmp_path)),
    ):
        # Run first ingestion (force rebuild to guarantee empty collection)
        report1 = await ingest_skills(force_rebuild=True)
        assert report1.chunks_total == 8  # 8 sections
        assert report1.chunks_new == 8
        assert report1.chunks_updated == 0
        assert report1.chunks_unchanged == 0
        assert len(report1.errors) == 0

        # Run second ingestion (should be completely idempotent - all unchanged)
        report2 = await ingest_skills(force_rebuild=False)
        assert report2.chunks_total == 8
        assert report2.chunks_new == 0
        assert report2.chunks_updated == 0
        assert report2.chunks_unchanged == 8
        assert len(report2.errors) == 0

        # Update mock file and re-run (should trigger update)
        updated_skill = mock_skill.replace(
            "Mock Board screen purpose.", "Mock Board updated screen purpose."
        )
        test_file.write_text(updated_skill, encoding="utf-8")

        report3 = await ingest_skills(force_rebuild=False)
        assert report3.chunks_total == 8
        assert report3.chunks_new == 0
        assert report3.chunks_updated == 1  # only Purpose section updated
        assert report3.chunks_unchanged == 7
        assert len(report3.errors) == 0

        # Force rebuild (should clear and treat all as new)
        report4 = await ingest_skills(force_rebuild=True)
        assert report4.chunks_total == 8
        assert report4.chunks_new == 8
        assert report4.chunks_updated == 0
        assert report4.chunks_unchanged == 0
        assert len(report4.errors) == 0
