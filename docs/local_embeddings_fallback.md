# Local Embedding Fallback (Reference)

Current: OpenAI text-embedding-3-small (1536-dim) for ChromaDB retrieval.

Swap path if speed becomes blocking:
1. Add sentence-transformers to runtime deps (already listed in v2-runtime)
2. Replace `clubos2/rag/embeddings.py` OpenAI call with:
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('BAAI/bge-small-en-v1.5')
   embeddings = model.encode(texts, normalize_embeddings=True)
   ```
3. Re-ingest all skill files (dimension change 1536 → 384):
   ```bash
   rm -rf var/chroma/
   python -m clubos2.rag.ingest
   ```
4. Re-establish baseline (3 back-to-back runs per methodology doc)

Cost: ~30 minutes one-time re-ingestion.

Trade-off: BGE-small slightly less accurate than text-embedding-3-small
but very close on ClubOS's small skill file corpus. No API cost after
initial setup; no rate limits.

Trigger: eval > 3 minutes wall-clock, budget concerns, or offline demo needed.
