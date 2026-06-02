"""Conversation memory for agent runs."""

from __future__ import annotations

from agentloop.types import Message, Role, ToolCall


class ConversationMemory:
    """Append-only message history with optional system prompt."""

    def __init__(self, system_prompt: str | None = None) -> None:
        self._system_prompt = system_prompt
        self._messages: list[Message] = []

    @property
    def messages(self) -> list[Message]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def add(self, message: Message) -> None:
        self._messages.append(message)

    def add_user(self, content: str) -> None:
        self.add(Message(role=Role.USER, content=content))

    def add_assistant(
        self,
        content: str | None,
        tool_calls: list[ToolCall] | None = None,
    ) -> None:
        self.add(
            Message(
                role=Role.ASSISTANT,
                content=content,
                tool_calls=tool_calls or [],
            )
        )

    def add_tool_result(self, tool_call_id: str, name: str, content: str) -> None:
        self.add(
            Message(
                role=Role.TOOL,
                content=content,
                tool_call_id=tool_call_id,
                name=name,
            )
        )

    def for_llm(self) -> list[Message]:
        out: list[Message] = []
        if self._system_prompt:
            out.append(Message(role=Role.SYSTEM, content=self._system_prompt))
        out.extend(self._messages)
        return out
