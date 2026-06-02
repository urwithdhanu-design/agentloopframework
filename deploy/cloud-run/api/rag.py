"""Pinecone vector search + OpenAI embeddings for RAG."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx

# Demo snippets when Pinecone is not configured (local dev without keys).
_MOCK_KB = [
    {
        "id": "mock-1",
        "text": "agentloop is a minimal Python framework for building LLM agents with tools and an observe-act loop.",
        "source": "docs/overview",
    },
    {
        "id": "mock-2",
        "text": "Deploy agentloop chatbots to Google Cloud Run by packaging FastAPI in a Docker container and exposing a /api/chat endpoint.",
        "source": "docs/deploy",
    },
    {
        "id": "mock-3",
        "text": "Pinecone stores document embeddings so the agent can retrieve relevant context before answering user questions.",
        "source": "docs/rag",
    },
]


@dataclass
class SearchHit:
    id: str
    text: str
    source: str
    score: float


class KnowledgeBase:
    """Vector search against Pinecone (or mock keyword search offline)."""

    def __init__(self) -> None:
        self.api_key = os.environ.get("PINECONE_API_KEY", "")
        self.index_name = os.environ.get("PINECONE_INDEX", "agentloop-kb")
        self.openai_key = os.environ.get("OPENAI_API_KEY", "")
        self.embedding_model = os.environ.get(
            "EMBEDDING_MODEL", "text-embedding-3-small"
        )
        self._index = None

        if self.api_key:
            from pinecone import Pinecone

            pc = Pinecone(api_key=self.api_key)
            self._index = pc.Index(self.index_name)

    @property
    def is_live(self) -> bool:
        return self._index is not None and bool(self.openai_key)

    async def embed(self, text: str) -> list[float]:
        if not self.openai_key:
            raise RuntimeError("OPENAI_API_KEY is required for embeddings.")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.embedding_model, "input": text},
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]

    async def search(self, query: str, top_k: int = 4) -> list[SearchHit]:
        if not self.is_live:
            return self._mock_search(query, top_k)

        vector = await self.embed(query)
        result = self._index.query(  # type: ignore[union-attr]
            vector=vector,
            top_k=top_k,
            include_metadata=True,
        )

        hits: list[SearchHit] = []
        for match in result.get("matches", []):
            meta = match.get("metadata") or {}
            hits.append(
                SearchHit(
                    id=str(match.get("id", "")),
                    text=str(meta.get("text", "")),
                    source=str(meta.get("source", "unknown")),
                    score=float(match.get("score") or 0.0),
                )
            )
        return hits

    def _mock_search(self, query: str, top_k: int) -> list[SearchHit]:
        words = set(query.lower().split())
        scored: list[tuple[float, dict]] = []
        for doc in _MOCK_KB:
            doc_words = set(doc["text"].lower().split())
            overlap = len(words & doc_words)
            scored.append((overlap / max(len(words), 1), doc))
        scored.sort(key=lambda x: x[0], reverse=True)

        hits: list[SearchHit] = []
        for score, doc in scored[:top_k]:
            hits.append(
                SearchHit(
                    id=doc["id"],
                    text=doc["text"],
                    source=doc["source"],
                    score=score,
                )
            )
        return hits

    def format_hits(self, hits: list[SearchHit]) -> str:
        if not hits:
            return json.dumps({"results": [], "message": "No relevant documents found."})

        payload = [
            {
                "source": hit.source,
                "score": round(hit.score, 4),
                "text": hit.text,
            }
            for hit in hits
        ]
        return json.dumps({"results": payload}, indent=2)
