"""pinecone-bridge — Hermes plugin.

Provides Pinecone search/upsert tools to skills. Reads PINECONE_API_KEY directly via
os.getenv (Hermes does NOT provide ctx.pinecone — verified §2.4.6).
"""
import os


def register(ctx):
    ctx.register_tool(
        name="pinecone_search",
        schema={
            "type": "function",
            "function": {
                "name": "pinecone_search",
                "description": "Semantic search across Solomon's 4 Pinecone namespaces. Returns ranked chunks with citation paths.",
                "parameters": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string"},
                        "namespace_weights": {
                            "type": "object",
                            "description": "Optional per-namespace weights (must sum to 1.0). Defaults from memory/pinecone-index.md."
                        },
                        "top_k": {"type": "integer", "default": 10}
                    }
                }
            }
        },
        handler=pinecone_search_handler,
    )


def pinecone_search_handler(args):
    """Implementation TBD — wire pinecone client + OpenAI embedding here.
    Returns a list of {chunk, score, namespace, citation_path}.
    """
    # from pinecone import Pinecone
    # client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    # ...
    return {"results": [], "note": "stub — implement per references/api-pinecone.md"}
