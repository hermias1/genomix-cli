"""Agent conversation loop with tool calling support."""
from __future__ import annotations
import json
from typing import Any, Callable

from genomix.providers.base import BaseProvider
from genomix.tools.registry import ToolRegistry
from genomix.agent.context_compressor import should_compress, compress_messages


class AgentLoop:
    def __init__(
        self,
        provider: BaseProvider,
        tool_registry: ToolRegistry,
        system_prompt: str = "",
        max_iterations: int = 30,
        on_tool_call: Callable[[str, dict], None] | None = None,
        on_tool_result: Callable[[str, str], None] | None = None,
        on_thinking: Callable[[str], None] | None = None,
    ):
        self.provider = provider
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.messages: list[dict[str, Any]] = []
        # UI callbacks
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result
        self.on_thinking = on_thinking

    def _build_messages(self) -> list[dict[str, Any]]:
        msgs = list(self.messages)

        # Compress if context is getting large
        max_tokens = self.provider.max_context_length()
        if should_compress(msgs, max_tokens):
            msgs = compress_messages(msgs, max_tokens)

        if self.system_prompt:
            return [{"role": "system", "content": self.system_prompt}] + msgs
        return msgs

    def chat(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        tools = self.tool_registry.list_tools() or None

        for iteration in range(self.max_iterations):
            all_messages = self._build_messages()

            if self.on_thinking and iteration == 0:
                self.on_thinking("Thinking...")

            response = self.provider.chat(all_messages, tools=tools)

            if response.tool_calls:
                self.messages.append({"role": "assistant", "content": response.content or "", "tool_calls": [
                    {"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": json.dumps(tc.arguments) if isinstance(tc.arguments, dict) else tc.arguments}}
                    for tc in response.tool_calls
                ]})
                for tc in response.tool_calls:
                    if self.on_tool_call:
                        self.on_tool_call(tc.name, tc.arguments)
                    try:
                        result = self.tool_registry.dispatch(tc.name, tc.arguments)
                    except Exception as e:
                        result = json.dumps({"error": str(e)})
                    # Truncate large tool results to prevent context explosion
                    if len(result) > 2000:
                        result = result[:2000] + "\n... [truncated]"
                    if self.on_tool_result:
                        self.on_tool_result(tc.name, result[:200])
                    self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            else:
                self.messages.append({"role": "assistant", "content": response.content})
                return response.content or ""

        return "Max iterations reached without a final response."
