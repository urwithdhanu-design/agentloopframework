"""
agentloop — a minimal, reusable agentic framework.

Quick start (offline, no API key):

    import asyncio
    from agentloop import Agent
    from agentloop.providers import MockProvider

    tools = ...
    provider = MockProvider(MockProvider.tool_then_answer("echo", {"text": "hi"}))
    agent = Agent.create(provider=provider, system="You are helpful.")
    agent.tools.register(echo)
    asyncio.run(agent.run("Say hi"))
"""

from agentloop.agent import Agent
from agentloop.events import AgentEvents
from agentloop.loop import AgentLoop
from agentloop.memory import ConversationMemory
from agentloop.tools import ToolRegistry
from agentloop.types import Message, Role, RunResult, ToolCall, ToolSpec

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "AgentEvents",
    "AgentLoop",
    "ConversationMemory",
    "Message",
    "Role",
    "RunResult",
    "ToolCall",
    "ToolRegistry",
    "ToolSpec",
    "__version__",
]
