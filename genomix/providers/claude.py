"""Claude (Anthropic) provider implementation."""
from __future__ import annotations
from typing import Any
import anthropic
from genomix.providers.base import BaseProvider, ProviderResponse, ToolCall

MODEL_CONTEXT = {"claude-sonnet-4-6": 200_000, "claude-opus-4-6": 200_000, "claude-haiku-4-5-20251001": 200_000}


class ClaudeProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> ProviderResponse:
        kwargs: dict[str, Any] = {"model": self.model, "max_tokens": 8192, "messages": messages}
        if tools:
            kwargs["tools"] = [self._convert_tool(t) for t in tools]
        response = self.client.messages.create(**kwargs)
        content = None
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(id=block.id, name=block.name, arguments=block.input))
        return ProviderResponse(content=content, tool_calls=tool_calls)

    def supports_tool_calling(self) -> bool:
        return True

    def max_context_length(self) -> int:
        return MODEL_CONTEXT.get(self.model, 200_000)

    @staticmethod
    def _convert_tool(tool: dict[str, Any]) -> dict[str, Any]:
        if "function" in tool:
            func = tool["function"]
            return {"name": func["name"], "description": func.get("description", ""), "input_schema": func.get("parameters", {"type": "object", "properties": {}})}
        return tool
