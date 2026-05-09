# pinecone-bridge

Exposes Pinecone search as a tool to skills. Used by Lane 1 of the 5-lane retrieval.

Reads `PINECONE_API_KEY` and `EMBEDDING_DIM` from env. Plugin manages its own Pinecone client (Hermes does not inject one — verified §2.4.6).

See `references/api-pinecone.md`.
