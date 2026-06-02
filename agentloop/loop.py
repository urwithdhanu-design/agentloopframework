"""Core observe–act agent loop."""

from __future__ import annotations

from agentloop.events import AgentEvents
from agentloop.memory import ConversationMemory
from agentloop.tools import ToolRegistry
from agentloop.types import Message, Role, RunResult


class AgentLoop:
    """
    Runs until the model returns text without tool calls, or max_iterations is hit.
    """

    def __init__(
        self,
        provider,
        *,
        tools: ToolRegistry | None = None,
        memory: ConversationMemory | None = None,
        max_iterations: int = 10,
        events: AgentEvents | None = None,
    ) -> None:
        self.provider = provider
        self.tools = tools or ToolRegistry()
        self.memory = memory or ConversationMemory()
        self.max_iterations = max_iterations
        self.events = events or AgentEvents()

    async def run(self, task: str) -> RunResult:
        await self.events.emit("run_start", task)
        self.memory.add_user(task)

        iterations = 0
        stopped_reason = "max_iterations"
        final_answer = ""

        while iterations < self.max_iterations:
            iterations += 1
            llm_messages = self.memory.for_llm()
            await self.events.emit("iteration", (iterations, llm_messages))

            tool_specs = self.tools.specs() if self.tools.specs() else None
            response = await self.provider.chat(llm_messages, tool_specs)
            await self.events.emit("llm_response", response)

            self.memory.add(
                Message(
                    role=Role.ASSISTANT,
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )

            if not response.tool_calls:
                final_answer = response.content or ""
                stopped_reason = "completed"
                break

            for call in response.tool_calls:
                await self.events.emit("tool_call", call)
                output = await self.tools.execute(call)
                await self.events.emit("tool_result", (call, output))
                self.memory.add_tool_result(call.id, call.name, output)

        result = RunResult(
            answer=final_answer,
            messages=self.memory.messages,
            iterations=iterations,
            stopped_reason=stopped_reason,
        )
        await self.events.emit("run_end", result)
        return result
