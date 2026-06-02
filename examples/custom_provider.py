"""
Plug in your own LLM by implementing chat(messages, tools) -> LLMResponse.
"""

import asyncio

from agentloop import Agent
from agentloop.types import LLMResponse, Message, ToolCall, ToolSpec


class EchoLLM:
    """Toy provider: always calls the first registered tool once, then answers."""

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> LLMResponse:
        user_text = next(
            (m.content for m in reversed(messages) if m.content),
            "",
        )
        if tools and "echo" in {t.name for t in tools} and "echo:" not in str(messages):
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(id="1", name="echo", arguments={"text": user_text or "hi"})
                ],
            )
        return LLMResponse(content=f"You said: {user_text}", tool_calls=[])


async def main() -> None:
    from agentloop.tools import ToolRegistry

    tools = ToolRegistry()

    @tools.register
    def echo(text: str) -> str:
        return text.upper()

    agent = Agent.create(provider=EchoLLM(), tools=tools)
    result = await agent.run("hello framework")
    print(result.answer)


if __name__ == "__main__":
    asyncio.run(main())
