"""High-level Agent builder for quick setup."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentloop.events import AgentEvents
from agentloop.loop import AgentLoop
from agentloop.memory import ConversationMemory
from agentloop.tools import ToolRegistry
from agentloop.types import RunResult


@dataclass
class Agent:
    """
    Fluent entry point for developers extending the framework.

    Example:
        agent = Agent.create(
            provider=OpenAICompatibleProvider(model="gpt-4o-mini"),
            system="You are a helpful assistant.",
        )
        agent.tools.register(my_tool)
        result = await agent.run("Summarize README.md")
    """

    loop: AgentLoop
    tools: ToolRegistry

    @classmethod
    def create(
        cls,
        provider: Any,
        *,
        system: str | None = None,
        max_iterations: int = 10,
        events: AgentEvents | None = None,
        tools: ToolRegistry | None = None,
    ) -> Agent:
        registry = tools or ToolRegistry()
        memory = ConversationMemory(system_prompt=system)
        loop = AgentLoop(
            provider,
            tools=registry,
            memory=memory,
            max_iterations=max_iterations,
            events=events,
        )
        return cls(loop=loop, tools=registry)

    async def run(self, task: str) -> RunResult:
        return await self.loop.run(task)

    def reset(self) -> None:
        self.loop.memory.clear()
