from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from datetime import UTC, datetime
from typing import Any

import chromadb
from pydantic import BaseModel, Field

from clubos2.rag.chunker import chunk_markdown_by_section
from clubos2.rag.embeddings import embed_texts


class IngestReport(BaseModel):
    collection: str
    chunks_total: int
    chunks_new: int
    chunks_updated: int
    chunks_unchanged: int
    duration_seconds: float
    errors: list[str] = Field(default_factory=list)


async def ingest_skills(force_rebuild: bool = False) -> IngestReport:
    """Walks the skills directory, chunks all markdown files, embeds them,

    and writes them to the ChromaDB 'clubos_skills' collection.
    """
    start_time = time.perf_counter()
    errors: list[str] = []

    # Get Chroma persist directory from env
    persist_dir = os.environ.get("CHROMA_PERSIST_DIR", "./var/chroma")
    chroma_client = chromadb.PersistentClient(path=persist_dir)

    collection_name = "clubos_skills"

    # Handle force rebuild
    if force_rebuild:
        try:
            chroma_client.delete_collection(collection_name)
        except Exception:
            pass

    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    current_dir = os.path.dirname(os.path.abspath(__file__))
    skills_dir = os.path.join(current_dir, "skills")

    if not os.path.exists(skills_dir):
        return IngestReport(
            collection=collection_name,
            chunks_total=0,
            chunks_new=0,
            chunks_updated=0,
            chunks_unchanged=0,
            duration_seconds=time.perf_counter() - start_time,
            errors=[f"Skills directory {skills_dir} does not exist."],
        )

    # Walk skills directory
    md_files = [
        os.path.join(skills_dir, f)
        for f in os.listdir(skills_dir)
        if f.endswith(".md") and f != "README.md"
    ]
    md_files.sort()

    chunks_total = 0
    chunks_new = 0
    chunks_updated = 0
    chunks_unchanged = 0

    to_write_chunks = []
    ids_to_delete = []

    # Process files
    for filepath in md_files:
        filename = os.path.basename(filepath)
        try:
            file_chunks = chunk_markdown_by_section(filepath)
            chunks_total += len(file_chunks)

            # Query existing database state for this file
            canonical_source = "skills." + os.path.splitext(filename)[0]
            existing = collection.get(where={"source": canonical_source})
            existing_ids = existing.get("ids", [])
            existing_metadatas = existing.get("metadatas", []) or []

            existing_id_set = set(existing_ids)
            existing_section_to_id = {
                meta["section"]: eid
                for eid, meta in zip(existing_ids, existing_metadatas, strict=False)
                if meta and "section" in meta
            }

            matched_existing_ids = set()

            for chunk in file_chunks:
                if chunk.chunk_id in existing_id_set:
                    chunks_unchanged += 1
                    matched_existing_ids.add(chunk.chunk_id)
                else:
                    # Content is new or changed.
                    # Check if section already exists for this file
                    if chunk.section in existing_section_to_id:
                        chunks_updated += 1
                        old_id = existing_section_to_id[chunk.section]
                        ids_to_delete.append(old_id)
                        matched_existing_ids.add(old_id)
                    else:
                        chunks_new += 1

                    to_write_chunks.append(chunk)

            # Any ID in existing_id_set that wasn't matched is an orphan and should be deleted
            orphans = existing_id_set - matched_existing_ids
            ids_to_delete.extend(list(orphans))

        except Exception as e:
            errors.append(f"Error processing {filename}: {e}")

    # Embed and write new/updated chunks
    if to_write_chunks:
        try:
            texts = [c.text for c in to_write_chunks]
            embeddings = await embed_texts(texts)

            write_ids = []
            write_embeddings: list[Any] = []
            write_documents = []
            write_metadatas: list[Any] = []

            timestamp = datetime.now(UTC).isoformat()

            for chunk, vector in zip(to_write_chunks, embeddings, strict=False):
                write_ids.append(chunk.chunk_id)
                write_embeddings.append(vector)
                write_documents.append(chunk.text)

                # Add default fields to metadata
                meta = dict(chunk.metadata)
                meta["type"] = "skill"
                meta["last_ingested"] = timestamp
                write_metadatas.append(meta)

            collection.upsert(
                ids=write_ids,
                embeddings=write_embeddings,
                documents=write_documents,
                metadatas=write_metadatas,
            )
        except Exception as e:
            errors.append(f"Failed to write chunks to ChromaDB: {e}")
            # Reset counters on error
            chunks_new = 0
            chunks_updated = 0

    # Delete orphans/replaced items
    if ids_to_delete:
        try:
            collection.delete(ids=ids_to_delete)
        except Exception as e:
            errors.append(f"Failed to delete orphan chunks: {e}")

    duration = time.perf_counter() - start_time
    return IngestReport(
        collection=collection_name,
        chunks_total=chunks_total,
        chunks_new=chunks_new,
        chunks_updated=chunks_updated,
        chunks_unchanged=chunks_unchanged,
        duration_seconds=duration,
        errors=errors,
    )


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    load_dotenv(".env.v2")

    parser = argparse.ArgumentParser(description="Ingest skill files into ChromaDB.")
    parser.add_argument(
        "target",
        choices=["skills"],
        help="Target to ingest (only 'skills' supported for now).",
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Drop the collection and rebuild from scratch.",
    )
    args = parser.parse_args()

    if args.target != "skills":
        print(f"Unsupported target: {args.target}", file=sys.stderr)
        sys.exit(1)

    try:
        report = asyncio.run(ingest_skills(force_rebuild=args.force_rebuild))
        print("=" * 60)
        print("ClubOS RAG Ingestion Report")
        print("=" * 60)
        print(f"Collection:      {report.collection}")
        print(f"Total Chunks:    {report.chunks_total}")
        print(f"New Chunks:      {report.chunks_new}")
        print(f"Updated Chunks:  {report.chunks_updated}")
        print(f"Unchanged:       {report.chunks_unchanged}")
        print(f"Duration (sec):  {report.duration_seconds:.2f}")

        if report.errors:
            print("-" * 60)
            print("Errors encountered:")
            for err in report.errors:
                print(f"- {err}")
            sys.exit(1)
        else:
            print("=" * 60)
            print("Ingestion completed successfully.")
            sys.exit(0)
    except Exception as e:
        print(f"Fatal error during ingestion: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
