"""Agent conversation loop with tool calling support."""
from __future__ import annotations
import json
from typing import Any

from genomix.providers.base import BaseProvider
from genomix.tools.registry import ToolRegistry


class AgentLoop:
    def __init__(
        self,
        provider: BaseProvider,
        tool_registry: ToolRegistry,
        system_prompt: str = "",
        max_iterations: int = 30,
    ):
        self.provider = provider
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.messages: list[dict[str, Any]] = []

    def _build_messages(self) -> list[dict[str, Any]]:
        if self.system_prompt:
            return [{"role": "system", "content": self.system_prompt}] + self.messages
        return list(self.messages)

    def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        tools = self.tool_registry.list_tools() or None

        for _ in range(self.max_iterations):
            all_messages = self._build_messages()
            response = self.provider.chat(all_messages, tools=tools)

            if response.tool_calls:
                self.messages.append({"role": "assistant", "content": response.content or "", "tool_calls": [
                    {"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": json.dumps(tc.arguments) if isinstance(tc.arguments, dict) else tc.arguments}}
                    for tc in response.tool_calls
                ]})
                for tc in response.tool_calls:
                    result = self.tool_registry.dispatch(tc.name, tc.arguments)
                    self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            else:
                self.messages.append({"role": "assistant", "content": response.content})
                return response.content or ""

        return "Max iterations reached without a final response."
