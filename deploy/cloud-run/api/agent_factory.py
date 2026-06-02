"""Build agentloop agents with Pinecone RAG tool."""

from __future__ import annotations

import os

from agentloop import Agent
from agentloop.providers import OpenAICompatibleProvider
from agentloop.tools import ToolRegistry

from api.rag import KnowledgeBase

SYSTEM_PROMPT = """You are a helpful knowledge-base assistant.

When the user asks about documentation, products, policies, or anything that may
exist in the company knowledge base, call search_knowledge_base first.

Ground your answer in the retrieved snippets. If nothing relevant is found, say so
clearly instead of inventing facts.

Keep answers concise and cite sources when available (use the 'source' field)."""


def create_rag_agent(kb: KnowledgeBase) -> Agent:
    tools = ToolRegistry()

    @tools.register(
        description=(
            "Search the Pinecone knowledge base for relevant document snippets. "
            "Use for factual questions about the product, docs, or policies."
        )
    )
    async def search_knowledge_base(query: str) -> str:
        hits = await kb.search(query, top_k=4)
        return kb.format_hits(hits)

    provider = OpenAICompatibleProvider(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL"),
    )

    return Agent.create(
        provider=provider,
        system=SYSTEM_PROMPT,
        tools=tools,
        max_iterations=6,
    )
