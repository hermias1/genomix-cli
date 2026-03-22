"""OpenAI API provider implementation."""
from __future__ import annotations
from typing import Any
import openai
from genomix.providers.base import BaseProvider, ProviderResponse, ToolCall

MODEL_CONTEXT = {"gpt-4o": 128_000, "gpt-4-turbo": 128_000, "o3": 200_000}


class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def chat(self, messages, tools=None):
        kwargs = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        response = self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        content = choice.message.content
        tool_calls = []
        if choice.message.tool_calls:
            import json
            for tc in choice.message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id, name=tc.function.name,
                    arguments=json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                ))
        return ProviderResponse(content=content, tool_calls=tool_calls)

    def chat_stream(self, messages, tools=None):
        from genomix.providers.base import TextDelta, ToolCallStart, ToolCallArgs, StreamDone
        kwargs = {"model": self.model, "messages": messages, "stream": True}
        if tools:
            kwargs["tools"] = tools
        stream = self.client.chat.completions.create(**kwargs)
        current_tool_ids = {}
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield TextDelta(text=delta.content)
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if tc.id:
                        current_tool_ids[idx] = tc.id
                    tc_id = current_tool_ids.get(idx, f"call_{idx}")
                    if tc.function and tc.function.name:
                        yield ToolCallStart(id=tc_id, name=tc.function.name)
                    if tc.function and tc.function.arguments:
                        yield ToolCallArgs(id=tc_id, partial_args=tc.function.arguments)
            if chunk.choices[0].finish_reason in ("stop", "tool_calls"):
                yield StreamDone()
                return
        yield StreamDone()

    def supports_tool_calling(self): return True
    def max_context_length(self): return MODEL_CONTEXT.get(self.model, 128_000)
