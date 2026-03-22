"""Claude (Anthropic) provider implementation."""
from __future__ import annotations
import json
from typing import Any
import anthropic
from genomix.providers.base import BaseProvider, ProviderResponse, ToolCall

MODEL_CONTEXT = {"claude-sonnet-4-6": 200_000, "claude-opus-4-6": 200_000, "claude-haiku-4-5-20251001": 200_000}


class ClaudeProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> ProviderResponse:
        kwargs = self.build_request(messages, tools=tools, model=self.model)
        response = self.client.messages.create(**kwargs)
        text_parts: list[str] = []
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(id=block.id, name=block.name, arguments=block.input))
        content = "\n".join(part for part in text_parts if part) or None
        return ProviderResponse(content=content, tool_calls=tool_calls)

    def supports_tool_calling(self) -> bool:
        return True

    def max_context_length(self) -> int:
        return MODEL_CONTEXT.get(self.model, 200_000)

    @classmethod
    def build_request(
        cls,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        model: str,
    ) -> dict[str, Any]:
        system_parts: list[str] = []
        anthropic_messages: list[dict[str, Any]] = []
        pending_tool_results: list[dict[str, Any]] = []

        for message in messages:
            role = message["role"]
            if role == "system":
                content = message.get("content")
                if content:
                    system_parts.append(str(content))
                continue

            if role == "tool":
                pending_tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": message["tool_call_id"],
                        "content": message.get("content", "") or "",
                    }
                )
                continue

            if pending_tool_results:
                anthropic_messages.append({"role": "user", "content": pending_tool_results})
                pending_tool_results = []

            if role == "assistant" and message.get("tool_calls"):
                anthropic_messages.append(
                    {
                        "role": "assistant",
                        "content": cls._assistant_content_blocks(message),
                    }
                )
                continue

            anthropic_messages.append(
                {
                    "role": role,
                    "content": message.get("content", "") or "",
                }
            )

        if pending_tool_results:
            anthropic_messages.append({"role": "user", "content": pending_tool_results})

        request: dict[str, Any] = {
            "model": model,
            "max_tokens": 8192,
            "messages": anthropic_messages,
        }
        if system_parts:
            request["system"] = "\n\n".join(system_parts)
        if tools:
            request["tools"] = [cls._convert_tool(t) for t in tools]
        return request

    @staticmethod
    def _assistant_content_blocks(message: dict[str, Any]) -> list[dict[str, Any]]:
        content: list[dict[str, Any]] = []
        text = message.get("content")
        if text:
            content.append({"type": "text", "text": text})

        for tool_call in message.get("tool_calls", []):
            arguments = tool_call.get("function", {}).get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            content.append(
                {
                    "type": "tool_use",
                    "id": tool_call["id"],
                    "name": tool_call["function"]["name"],
                    "input": arguments,
                }
            )
        return content

    @staticmethod
    def _convert_tool(tool: dict[str, Any]) -> dict[str, Any]:
        if "function" in tool:
            func = tool["function"]
            return {"name": func["name"], "description": func.get("description", ""), "input_schema": func.get("parameters", {"type": "object", "properties": {}})}
        return tool
