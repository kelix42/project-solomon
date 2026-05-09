# Pinecone — vector memory

## Setup

1. Sign up at https://www.pinecone.io. Pick the serverless tier.
2. Get an API key. Store in `.env` as `PINECONE_API_KEY`.
3. `install.sh` step 9 creates the index named `PINECONE_INDEX_NAME` (default `solomon`) with `dimension=EMBEDDING_DIM` (default 3072), `metric=cosine`, region `PINECONE_REGION` (default `us-east-1`).

## Embedding

OpenAI `text-embedding-3-large` at 3072 dimensions. `EMBEDDING_DIM` must match the Pinecone index dim — install.sh validates.

## Namespaces (4)

- `solomon-corpus-wiki` — wiki page sections; vector ID `"wiki:" + slug + ":" + section_hash`. Weight 0.40.
- `solomon-corpus-raw` — raw chunks (sliding window, 800 tokens / 100 overlap); vector ID `sha256(file)[:16] + ":" + chunk_index`. Weight 0.20.
- `solomon-captured-items` — owner-rule rows; vector ID `"captured:" + row.id`. Weight 0.30.
- `solomon-decision-log` — decision-log entries; vector ID `"decision:" + sha256(entry_body) + ":0"`. Weight 0.10.

## Concurrent writes

`db/.pinecone-write.lock` (file lock) — at most one Pinecone write process in-flight, ever. `solomon-corpus-ingest` and Sleep-Cycle Job 11 both acquire it.

## Failure handling

Per §2.4.7: 5xx / network → empty retrieval, pipeline continues with non-retrieval context. Job 11 marks rows as not-yet-embedded and retries next night. Three consecutive nights of failure → Telegram alert.
