"""LLM provider protocol."""

from __future__ import annotations

from typing import Protocol

from agentloop.types import LLMResponse, Message, ToolSpec


class LLMProvider(Protocol):
    """Implement to plug in OpenAI, Anthropic, local models, etc."""

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> LLMResponse: ...
