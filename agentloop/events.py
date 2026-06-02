"""Lifecycle hooks for observability and control."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from agentloop.types import LLMResponse, Message, RunResult, ToolCall


@dataclass
class AgentEvents:
    """Optional callbacks; sync or async handlers are supported."""

    on_run_start: Callable[[str], Any] | None = None
    on_iteration: Callable[[int, list[Message]], Any] | None = None
    on_llm_response: Callable[[LLMResponse], Any] | None = None
    on_tool_call: Callable[[ToolCall], Any] | None = None
    on_tool_result: Callable[[ToolCall, str], Any] | None = None
    on_run_end: Callable[[RunResult], Any] | None = None
    _hooks: list[Callable[[str, Any], Awaitable[None] | None]] = field(
        default_factory=list, repr=False
    )

    def subscribe(self, hook: Callable[[str, Any], Awaitable[None] | None]) -> None:
        """Generic hook: hook(event_name, payload)."""
        self._hooks.append(hook)

    async def emit(self, event: str, payload: Any) -> None:
        for hook in self._hooks:
            result = hook(event, payload)
            if result is not None and hasattr(result, "__await__"):
                await result

        handler_map = {
            "run_start": self.on_run_start,
            "iteration": self.on_iteration,
            "llm_response": self.on_llm_response,
            "tool_call": self.on_tool_call,
            "tool_result": self.on_tool_result,
            "run_end": self.on_run_end,
        }
        handler = handler_map.get(event)
        if handler is None:
            return
        if event == "run_start":
            result = handler(payload)
        elif event == "iteration":
            iteration, messages = payload
            result = handler(iteration, messages)
        elif event == "llm_response":
            result = handler(payload)
        elif event == "tool_call":
            result = handler(payload)
        elif event == "tool_result":
            call, tool_output = payload
            result = handler(call, tool_output)
        elif event == "run_end":
            result = handler(payload)
        else:
            return
        if result is not None and hasattr(result, "__await__"):
            await result
