"""AI provider factory."""
from __future__ import annotations
from typing import Any
from genomix.providers.base import BaseProvider


def get_provider(name: str, **kwargs: Any) -> BaseProvider:
    if name == "claude":
        from genomix.providers.claude import ClaudeProvider
        return ClaudeProvider(api_key=kwargs.get("api_key", ""), model=kwargs.get("model", "claude-sonnet-4-6"))
    elif name == "openai":
        from genomix.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=kwargs.get("api_key", ""), model=kwargs.get("model", "gpt-4o"))
    elif name == "opencode":
        from genomix.providers.opencode import OpenCodeProvider
        return OpenCodeProvider(endpoint=kwargs.get("endpoint", "http://localhost:11434"), model=kwargs.get("model", "llama3.3:70b"))
    else:
        raise ValueError(f"Unknown provider: {name}")
