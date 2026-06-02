"""OpenAI-compatible chat completions (OpenAI, Azure, Ollama, vLLM, etc.)."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

from agentloop.types import LLMResponse, Message, ToolCall, ToolSpec

try:
    import httpx
except ImportError as exc:
    raise ImportError(
        "OpenAI-compatible provider requires httpx. Install with: pip install agentloop[openai]"
    ) from exc


class OpenAICompatibleProvider:
    """Calls POST /v1/chat/completions on an OpenAI-compatible API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
        timeout: float = 120.0,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.model = model
        self.timeout = timeout
        self.extra_headers = extra_headers or {}

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolSpec] | None = None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [_serialize_message(m) for m in messages],
        }
        if tools:
            payload["tools"] = [t.to_openai_tool() for t in tools]
            payload["tool_choice"] = "auto"

        headers = {"Content-Type": "application/json", **self.extra_headers}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choice = data["choices"][0]["message"]
        tool_calls = _parse_tool_calls(choice.get("tool_calls") or [])
        return LLMResponse(
            content=choice.get("content"),
            tool_calls=tool_calls,
            raw=data,
        )


def _serialize_message(message: Message) -> dict[str, Any]:
    out = message.to_dict()
    if message.tool_calls:
        out["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.name,
                    "arguments": json.dumps(tc.arguments),
                },
            }
            for tc in message.tool_calls
        ]
    return out


def _parse_tool_calls(raw_calls: list[dict[str, Any]]) -> list[ToolCall]:
    parsed: list[ToolCall] = []
    for item in raw_calls:
        fn = item.get("function", {})
        args_raw = fn.get("arguments", "{}")
        if isinstance(args_raw, str):
            try:
                args = json.loads(args_raw) if args_raw else {}
            except json.JSONDecodeError:
                args = {"raw": args_raw}
        else:
            args = args_raw
        parsed.append(
            ToolCall(
                id=item.get("id") or str(uuid.uuid4()),
                name=fn.get("name", ""),
                arguments=args,
            )
        )
    return parsed
