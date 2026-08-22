from __future__ import annotations

import hashlib
import os
from typing import Any

import tiktoken
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    text: str
    source: str
    section: str
    chunk_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


def count_tokens(text: str) -> int:
    """Helper to count tokens in a text using cl100k_base encoding."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Fallback approximation: ~4 characters per token if tiktoken fails
        return len(text) // 4


def generate_chunk_id(source: str, section: str, text: str) -> str:
    """Generates a stable chunk ID using a SHA-256 hash of the content."""
    payload = f"{source}:{section}:{text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def split_section_into_subchunks(section_text: str, max_tokens: int = 800) -> list[str]:
    """Splits a long section at paragraph boundaries (\\n\\n) into sub-chunks.

    Ensures code blocks are not split.
    """
    paragraphs = section_text.split("\n\n")
    subchunks: list[str] = []

    current_paragraphs: list[str] = []
    current_tokens = 0
    in_code_block = False

    for paragraph in paragraphs:
        # Check code block toggle count in this paragraph
        code_block_count = paragraph.count("```")
        # If code_block_count is odd, toggle state
        if code_block_count % 2 == 1:
            in_code_block = not in_code_block

        p_tokens = count_tokens(paragraph)

        # If adding this paragraph exceeds limits (and we are not inside a code block),
        # flush the current accumulator.
        if current_paragraphs and (current_tokens + p_tokens > max_tokens) and not in_code_block:
            subchunks.append("\n\n".join(current_paragraphs))
            current_paragraphs = [paragraph]
            current_tokens = p_tokens
        else:
            current_paragraphs.append(paragraph)
            current_tokens += p_tokens

    if current_paragraphs:
        subchunks.append("\n\n".join(current_paragraphs))

    return subchunks


def chunk_markdown_by_section(path: str) -> list[Chunk]:
    """Splits a markdown file at ## headings. Each section becomes one or more chunks.

    Intro text before the first ## heading belongs to the 'Overview' section.
    If a section exceeds 800 tokens, it is split at paragraph boundaries.
    """
    source = "skills." + os.path.splitext(os.path.basename(path))[0]
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Split lines
    lines = content.splitlines()
    sections: list[tuple[str, list[str]]] = []

    current_section_name = "Overview"
    current_section_lines: list[str] = []

    for line in lines:
        if line.startswith("## "):
            # Flush current section
            if current_section_lines:
                sections.append((current_section_name, current_section_lines))
            current_section_name = line[3:].strip()
            current_section_lines = []
        elif line.startswith("# "):
            # Screen Name heading, skip or include in Overview
            pass
        else:
            current_section_lines.append(line)

    if current_section_lines:
        sections.append((current_section_name, current_section_lines))

    chunks: list[Chunk] = []

    for section_name, section_lines in sections:
        section_text = "\n".join(section_lines).strip()
        if not section_text:
            continue

        tokens = count_tokens(section_text)

        if tokens <= 800:
            text_blocks = [section_text]
        else:
            text_blocks = split_section_into_subchunks(section_text, max_tokens=800)

        for text_block in text_blocks:
            chunk_id = generate_chunk_id(source, section_name, text_block)
            metadata = {
                "source": source,
                "section": section_name,
            }
            chunks.append(
                Chunk(
                    text=text_block,
                    source=source,
                    section=section_name,
                    chunk_id=chunk_id,
                    metadata=metadata,
                )
            )

    return chunks
