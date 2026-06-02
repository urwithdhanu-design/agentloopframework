"""Load documents into Pinecone for the RAG chatbot.

Usage (from repo root):
    pip install -r deploy/cloud-run/requirements.txt
    set OPENAI_API_KEY=sk-...
    set PINECONE_API_KEY=...
    set PINECONE_INDEX=agentloop-kb
    python deploy/cloud-run/scripts/ingest.py

Create the Pinecone index first (dimension 1536 for text-embedding-3-small).
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Repo root on path for agentloop + api imports
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "deploy" / "cloud-run"))

from api.rag import KnowledgeBase  # noqa: E402

SAMPLE_DOCS = [
    {
        "source": "docs/overview",
        "text": "agentloop is a minimal Python framework for building LLM agents with tools, memory, and an observe-act loop.",
    },
    {
        "source": "docs/tools",
        "text": "Register tools with @tools.register. The agent loop calls the LLM, executes tool calls, and feeds results back until a final answer is ready.",
    },
    {
        "source": "docs/deploy",
        "text": "Package the FastAPI backend and React UI in Docker, deploy to Google Cloud Run, and expose POST /api/chat for the chat UI.",
    },
    {
        "source": "docs/pinecone",
        "text": "Pinecone stores vector embeddings of your documents. The search_knowledge_base tool retrieves the top matches and grounds the LLM response.",
    },
    {
        "source": "docs/react",
        "text": "The React chat UI sends messages to /api/chat with a session_id so the server keeps multi-turn conversation memory via agentloop.",
    },
]


async def main() -> None:
    kb = KnowledgeBase()
    if not kb.api_key:
        raise SystemExit("PINECONE_API_KEY is required.")
    if not kb.openai_key:
        raise SystemExit("OPENAI_API_KEY is required for embeddings.")

    from pinecone import Pinecone

    pc = Pinecone(api_key=kb.api_key)
    index = pc.Index(kb.index_name)

    vectors = []
    for doc in SAMPLE_DOCS:
        embedding = await kb.embed(doc["text"])
        vectors.append(
            {
                "id": str(uuid.uuid4()),
                "values": embedding,
                "metadata": {"text": doc["text"], "source": doc["source"]},
            }
        )

    index.upsert(vectors=vectors)
    print(f"Upserted {len(vectors)} documents into index '{kb.index_name}'.")


if __name__ == "__main__":
    asyncio.run(main())
