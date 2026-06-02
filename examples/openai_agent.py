"""
Live agent with an OpenAI-compatible API.

Set OPENAI_API_KEY (and optionally OPENAI_BASE_URL, model name below).

    pip install -e ".[openai]"
    python examples/openai_agent.py
"""

import asyncio
import os

from agentloop import Agent, AgentEvents
from agentloop.providers import OpenAICompatibleProvider
from agentloop.tools import ToolRegistry


def main() -> None:
    tools = ToolRegistry()

    @tools.register(description="Add two numbers.")
    def add(a: int, b: int) -> int:
        return a + b

    events = AgentEvents()

    def on_tool(call):
        print(f"  [tool] {call.name}({call.arguments})")

    events.on_tool_call = on_tool

    provider = OpenAICompatibleProvider(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
    )

    agent = Agent.create(
        provider=provider,
        system="You are a helpful math assistant. Use the add tool when appropriate.",
        tools=tools,
        events=events,
        max_iterations=8,
    )

    async def run() -> None:
        result = await agent.run("What is 17 + 25? Use the add tool.")
        print("\nAnswer:", result.answer)
        print("Stopped:", result.stopped_reason)

    asyncio.run(run())


if __name__ == "__main__":
    main()
