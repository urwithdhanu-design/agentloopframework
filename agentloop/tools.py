"""Tool registry and execution."""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from typing import Any

from agentloop.types import ToolCall, ToolSpec


class ToolRegistry:
    """Register callables as LLM-invokable tools."""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._specs: dict[str, ToolSpec] = {}

    def register(
        self,
        func: Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> Callable[..., Any]:
        """Decorator or direct registration for a tool handler."""

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            tool_name = name or fn.__name__
            tool_desc = description or (fn.__doc__ or "").strip() or f"Tool {tool_name}"
            tool_params = parameters or _infer_parameters_schema(fn)
            self._handlers[tool_name] = fn
            self._specs[tool_name] = ToolSpec(
                name=tool_name,
                description=tool_desc,
                parameters=tool_params,
            )
            return fn

        if func is not None:
            return decorator(func)
        return decorator

    def add(
        self,
        name: str,
        handler: Callable[..., Any],
        *,
        description: str,
        parameters: dict[str, Any],
    ) -> None:
        self._handlers[name] = handler
        self._specs[name] = ToolSpec(
            name=name, description=description, parameters=parameters
        )

    def specs(self) -> list[ToolSpec]:
        return list(self._specs.values())

    def has(self, name: str) -> bool:
        return name in self._handlers

    async def execute(self, call: ToolCall) -> str:
        if call.name not in self._handlers:
            return json.dumps({"error": f"Unknown tool: {call.name}"})
        handler = self._handlers[call.name]
        try:
            result = handler(**call.arguments)
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, str):
                return result
            return json.dumps(result, default=str)
        except Exception as exc:
            return json.dumps({"error": str(exc), "tool": call.name})


def _infer_parameters_schema(fn: Callable[..., Any]) -> dict[str, Any]:
    sig = inspect.signature(fn)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for param_name, param in sig.parameters.items():
        if param_name in ("self", "cls"):
            continue
        prop: dict[str, Any] = {"type": "string"}
        if param.annotation is not inspect.Parameter.empty:
            if param.annotation is int:
                prop["type"] = "integer"
            elif param.annotation is float:
                prop["type"] = "number"
            elif param.annotation is bool:
                prop["type"] = "boolean"
            elif param.annotation is dict:
                prop["type"] = "object"
            elif param.annotation is list:
                prop["type"] = "array"
        properties[param_name] = prop
        if param.default is inspect.Parameter.empty:
            required.append(param_name)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }
