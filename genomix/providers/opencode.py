"""OpenCode (Ollama) local provider implementation."""
from __future__ import annotations
import json
from typing import Any
import httpx
from genomix.providers.base import BaseProvider, ProviderResponse, ToolCall


class OpenCodeProvider(BaseProvider):
    def __init__(self, endpoint: str = "http://localhost:11434", model: str = "llama3.3:70b"):
        self.endpoint = endpoint.rstrip("/")
        self.model = model

    def chat(self, messages, tools=None):
        payload = {"model": self.model, "messages": messages, "stream": False}
        if tools:
            payload["tools"] = tools
        with httpx.Client(timeout=120) as client:
            resp = client.post(f"{self.endpoint}/v1/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
        choice = data["choices"][0]
        content = choice["message"].get("content")
        tool_calls = []
        for tc in choice["message"].get("tool_calls", []):
            args = tc["function"]["arguments"]
            if isinstance(args, str):
                args = json.loads(args)
            tool_calls.append(ToolCall(id=tc.get("id", ""), name=tc["function"]["name"], arguments=args))
        return ProviderResponse(content=content, tool_calls=tool_calls)

    def supports_tool_calling(self): return True
    def max_context_length(self): return 32_000
