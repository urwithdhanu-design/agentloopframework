"""
Run without an API key using MockProvider.

    python examples/basic_mock.py
"""

import asyncio

from agentloop import Agent
from agentloop.providers import MockProvider
from agentloop.tools import ToolRegistry


def main() -> None:
    tools = ToolRegistry()

    @tools.register(description="Return the current weather for a city (demo).")
    def get_weather(city: str) -> dict:
        return {"city": city, "temp_c": 22, "conditions": "sunny"}

    script = MockProvider.tool_then_answer(
        "get_weather",
        {"city": "Paris"},
        final="It's 22°C and sunny in Paris.",
    )

    agent = Agent.create(
        provider=MockProvider(script),
        system="You are a concise assistant. Use tools when needed.",
        tools=tools,
    )

    async def run() -> None:
        result = await agent.run("What's the weather in Paris?")
        print("Answer:", result.answer)
        print("Iterations:", result.iterations)
        print("Reason:", result.stopped_reason)

    asyncio.run(run())


if __name__ == "__main__":
    main()
