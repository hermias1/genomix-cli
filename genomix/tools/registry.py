"""Centralized tool registry for Genomix."""
from __future__ import annotations
from typing import Any, Callable


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, dict[str, Any]] = {}

    def register(self, name: str, description: str, parameters: dict[str, Any], handler: Callable[[dict[str, Any]], str]) -> None:
        self._tools[name] = {
            "schema": {"type": "function", "function": {"name": name, "description": description, "parameters": parameters}},
            "handler": handler,
        }

    def list_tools(self) -> list[dict[str, Any]]:
        return [t["schema"] for t in self._tools.values()]

    def dispatch(self, name: str, arguments: dict[str, Any]) -> str:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]["handler"](arguments)

    def has_tool(self, name: str) -> bool:
        return name in self._tools
