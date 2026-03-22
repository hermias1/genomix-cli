"""Ollama local provider implementation."""
from __future__ import annotations
import json
import os
from typing import Any
import httpx
from genomix.providers.base import BaseProvider, ProviderResponse, ToolCall


class OpenCodeProvider(BaseProvider):
    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        model: str = "qwen3-coder:30b",
        timeout_seconds: float | None = None,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else _default_timeout_seconds()

    def _http_timeout(self) -> httpx.Timeout:
        # Local 30B-class models can legitimately take several minutes on larger prompts.
        return httpx.Timeout(connect=10.0, read=self.timeout_seconds, write=self.timeout_seconds, pool=10.0)

    def chat(self, messages, tools=None):
        # Clean messages: ensure content is always a string (Ollama requires it)
        clean_messages = []
        for m in messages:
            msg = {k: v for k, v in m.items() if k in ("role", "content", "tool_call_id", "tool_calls")}
            if msg.get("content") is None:
                msg["content"] = ""
            clean_messages.append(msg)

        payload = {"model": self.model, "messages": clean_messages, "stream": False}
        if tools:
            payload["tools"] = tools
        try:
            with httpx.Client(timeout=self._http_timeout()) as client:
                resp = client.post(f"{self.endpoint}/v1/chat/completions", json=payload)
                if resp.status_code != 200:
                    # Fall back to no-tools call if tools cause issues
                    if tools:
                        payload.pop("tools", None)
                        resp = client.post(f"{self.endpoint}/v1/chat/completions", json=payload)
                    resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Ollama request timed out after {self.timeout_seconds:.0f}s. "
                "Increase GENOMIX_OLLAMA_TIMEOUT_SECONDS or reduce prompt/tool load."
            ) from exc
        choice = data["choices"][0]
        content = choice["message"].get("content")
        tool_calls = []
        for tc in choice["message"].get("tool_calls", []):
            args = tc["function"]["arguments"]
            if isinstance(args, str):
                args = json.loads(args)
            tool_calls.append(ToolCall(id=tc.get("id", ""), name=tc["function"]["name"], arguments=args))
        return ProviderResponse(content=content, tool_calls=tool_calls)

    def chat_stream(self, messages, tools=None):
        raise NotImplementedError

    def supports_tool_calling(self): return True
    def max_context_length(self): return 16_000  # Conservative to trigger compression early


def _default_timeout_seconds() -> float:
    value = os.environ.get("GENOMIX_OLLAMA_TIMEOUT_SECONDS", "900")
    try:
        return float(value)
    except ValueError:
        return 900.0
