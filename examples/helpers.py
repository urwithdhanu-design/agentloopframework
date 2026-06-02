"""Shared tools and agent factory for examples."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime

from agentloop import Agent, AgentEvents
from agentloop.providers import OpenAICompatibleProvider
from agentloop.tools import ToolRegistry
from agentloop.types import LLMResponse, Message, Role, ToolCall, ToolSpec


def build_tools() -> ToolRegistry:
    tools = ToolRegistry()

    @tools.register(description="Return the current local date and time.")
    def get_current_time() -> str:
        return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    @tools.register(
        description="Evaluate a math expression. Supports +, -, *, /, and parentheses."
    )
    def calculate(expression: str) -> str:
        allowed = set("0123456789+-*/(). ")
        if not set(expression).issubset(allowed):
            return json.dumps({"error": "Only numbers and + - * / ( ) are allowed."})
        try:
            result = eval(expression, {"__builtins__": {}}, {})  # noqa: S307 — demo only
            return str(result)
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    return tools


class MockChatProvider:
    """
    Offline provider for demos: uses simple rules to call tools, then summarize results.
    """

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> LLMResponse:
        if not messages:
            return LLMResponse(content="Hello! How can I help?", tool_calls=[])

        last = messages[-1]
        if last.role == Role.TOOL:
            return LLMResponse(
                content=f"Here is what I found: {last.content}",
                tool_calls=[],
            )

        user_text = _last_user_text(messages)
        lowered = user_text.lower()

        if any(word in lowered for word in ("time", "date", "today", "clock")):
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(id="call_time", name="get_current_time", arguments={})
                ],
            )

        expression = _extract_math_expression(user_text)
        if expression:
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(
                        id="call_calc",
                        name="calculate",
                        arguments={"expression": expression},
                    )
                ],
            )

        if "hello" in lowered or "hi" in lowered:
            return LLMResponse(
                content=(
                    "Hello! I'm running in mock mode (no API key). "
                    "Ask me for the time or a calculation like 'what is 24 * 17'."
                ),
                tool_calls=[],
            )

        return LLMResponse(
            content=(
                f"I heard: \"{user_text}\". In mock mode I can tell the time or do math. "
                "Try: 'What time is it?' or 'Calculate 100 / 4'."
            ),
            tool_calls=[],
        )


def _last_user_text(messages: list[Message]) -> str:
    for message in reversed(messages):
        if message.role == Role.USER and message.content:
            return message.content
    return ""


def _extract_math_expression(text: str) -> str | None:
    cleaned = re.sub(
        r"(?i)(what is|calculate|compute|solve|equals?|=\s*$)",
        "",
        text,
    ).strip()
    candidate = re.sub(r"[^0-9+\-*/(). ]", "", cleaned).strip()
    if candidate and re.search(r"\d", candidate) and re.search(r"[\+\-\*/]", candidate):
        return candidate
    return None


def create_chat_agent(
    *,
    mode: str = "auto",
    system: str | None = None,
    events: AgentEvents | None = None,
) -> Agent:
    """
    mode: 'mock' | 'live' | 'auto' (live when OPENAI_API_KEY is set, else mock)
    """
    tools = build_tools()
    resolved = mode
    if resolved == "auto":
        resolved = "live" if os.environ.get("OPENAI_API_KEY") else "mock"

    default_system = (
        "You are a friendly assistant in a conversation. "
        "Use tools when the user asks for the time or math. "
        "Keep replies concise and natural."
    )

    if resolved == "live":
        provider = OpenAICompatibleProvider(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        )
    else:
        provider = MockChatProvider()

    return Agent.create(
        provider=provider,
        system=system or default_system,
        tools=tools,
        events=events,
        max_iterations=8,
    )
