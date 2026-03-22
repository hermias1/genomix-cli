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

    def _force_final_synthesis_stream(self):
        from genomix.providers.base import TextDelta, StreamDone
        self.messages.append({
            "role": "user",
            "content": "You have enough information. Do not call any more tools. Provide the best final answer now.",
        })
        yielded_text = False
        for event in self.provider.chat_stream(self._build_messages(), tools=None):
            if isinstance(event, TextDelta):
                yielded_text = True
                yield event
            elif isinstance(event, StreamDone):
                if not yielded_text:
                    yield TextDelta(text="Max iterations reached without a final response.")
                yield event
                return
        if not yielded_text:
            yield TextDelta(text="Max iterations reached without a final response.")
        yield StreamDone()

    def chat_stream(self, user_message: str):
        """Stream events from the agent loop."""
        from genomix.providers.base import (
            TextDelta, ToolCallStart, ToolCallArgs, ToolCallComplete,
            ToolResult, ErrorEvent, StreamDone,
        )
        self.messages.append({"role": "user", "content": user_message})
        tools = self.tool_registry.list_tools() or None

        for iteration in range(self.max_iterations):
            all_messages = self._build_messages()
            accumulated_text = ""
            pending_tool_calls = {}  # id -> {name, args}

            for event in self.provider.chat_stream(all_messages, tools=tools):
                if isinstance(event, TextDelta):
                    accumulated_text += event.text
                    yield event
                elif isinstance(event, ToolCallStart):
                    pending_tool_calls[event.id] = {"name": event.name, "args": ""}
                    yield event
                elif isinstance(event, ToolCallArgs):
                    if event.id in pending_tool_calls:
                        pending_tool_calls[event.id]["args"] += event.partial_args
                elif isinstance(event, StreamDone):
                    break

            if pending_tool_calls:
                # Store assistant message with tool calls
                tool_calls_msg = []
                for tc_id, tc_data in pending_tool_calls.items():
                    tool_calls_msg.append({
                        "id": tc_id, "type": "function",
                        "function": {
                            "name": tc_data["name"],
                            "arguments": tc_data["args"] if isinstance(tc_data["args"], str) else json.dumps(tc_data["args"]),
                        }
                    })
                self.messages.append({"role": "assistant", "content": accumulated_text or "", "tool_calls": tool_calls_msg})

                for tc_id, tc_data in pending_tool_calls.items():
                    try:
                        args = json.loads(tc_data["args"]) if tc_data["args"] else {}
                    except json.JSONDecodeError:
                        args = {}
                    yield ToolCallComplete(id=tc_id, name=tc_data["name"], arguments=args)

                    if self.on_tool_call:
                        self.on_tool_call(tc_data["name"], args)

                    try:
                        result = self.tool_registry.dispatch(tc_data["name"], args)
                    except Exception as e:
                        result = json.dumps({"error": str(e)})
                    if len(result) > 2000:
                        result = result[:2000] + "\n... [truncated]"
                    yield ToolResult(tool_name=tc_data["name"], result=result[:200])
                    if self.on_tool_result:
                        self.on_tool_result(tc_data["name"], result[:200])
                    self.messages.append({"role": "tool", "tool_call_id": tc_id, "content": result})
                continue
            else:
                self.messages.append({"role": "assistant", "content": accumulated_text})
                yield StreamDone()
                return

        # Max iterations
        yield from self._force_final_synthesis_stream()

    def chat(self, user_message: str) -> str:
        from genomix.providers.base import TextDelta
        full_text = ""
        for event in self.chat_stream(user_message):
            if isinstance(event, TextDelta):
                full_text += event.text
        return full_text
