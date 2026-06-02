"""Deterministic mock provider for tests and offline examples."""

from __future__ import annotations

from agentloop.types import LLMResponse, Message, Role, ToolCall, ToolSpec


class MockProvider:
    """
    Scripted responses: each chat() consumes the next script entry.
    Entry: str (final answer), or list[ToolCall], or LLMResponse.
    """

    def __init__(self, script: list[str | list[ToolCall] | LLMResponse]) -> None:
        self._script = list(script)
        self._index = 0

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> LLMResponse:
        if self._index >= len(self._script):
            return LLMResponse(content="Done.", tool_calls=[])

        entry = self._script[self._index]
        self._index += 1

        if isinstance(entry, LLMResponse):
            return entry
        if isinstance(entry, str):
            return LLMResponse(content=entry, tool_calls=[])
        return LLMResponse(content=None, tool_calls=entry)

    @staticmethod
    def tool_then_answer(
        tool_name: str,
        arguments: dict,
        *,
        call_id: str = "call_1",
        final: str = "Task complete.",
    ) -> list[str | list[ToolCall]]:
        return [
            [ToolCall(id=call_id, name=tool_name, arguments=arguments)],
            final,
        ]
