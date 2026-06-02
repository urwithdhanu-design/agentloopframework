import pytest

from agentloop import Agent
from agentloop.providers import MockProvider


@pytest.fixture
def echo_tool():
    registry_tools = __import__("agentloop.tools", fromlist=["ToolRegistry"]).ToolRegistry()

    @registry_tools.register(description="Echo text back")
    def echo(text: str) -> str:
        return f"echo:{text}"

    return registry_tools, echo


@pytest.mark.asyncio
async def test_tool_then_answer(echo_tool):
    tools, _ = echo_tool
    script = MockProvider.tool_then_answer(
        "echo",
        {"text": "hello"},
        final="The echo tool returned hello.",
    )
    agent = Agent.create(
        provider=MockProvider(script),
        system="Test agent",
        tools=tools,
    )
    result = await agent.run("Please echo hello")

    assert result.stopped_reason == "completed"
    assert result.iterations == 2
    assert "hello" in result.answer.lower() or "echo" in result.answer.lower()


@pytest.mark.asyncio
async def test_direct_answer():
    agent = Agent.create(
        provider=MockProvider(["Direct answer without tools."]),
        system="Test",
    )
    result = await agent.run("Hi")
    assert result.stopped_reason == "completed"
    assert result.iterations == 1
    assert result.answer == "Direct answer without tools."
