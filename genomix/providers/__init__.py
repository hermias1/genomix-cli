"""AI provider factory."""
from __future__ import annotations
from typing import Any
from genomix.providers.base import BaseProvider

# Canonical provider names
SUPPORTED_PROVIDERS = {"claude", "openai", "ollama"}

# Aliases for backward compatibility
_ALIASES = {"opencode": "ollama"}


def get_provider(name: str, **kwargs: Any) -> BaseProvider:
    """Create a provider instance by name."""
    name = _ALIASES.get(name, name)

    if name == "claude":
        from genomix.providers.claude import ClaudeProvider
        return ClaudeProvider(
            api_key=kwargs.get("api_key", ""),
            model=kwargs.get("model", "claude-sonnet-4-6"),
        )
    elif name == "openai":
        from genomix.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=kwargs.get("api_key", ""),
            model=kwargs.get("model", "gpt-4o"),
        )
    elif name == "ollama":
        from genomix.providers.opencode import OpenCodeProvider
        return OpenCodeProvider(
            endpoint=kwargs.get("endpoint", "http://localhost:11434"),
            model=kwargs.get("model", "qwen3-coder:30b"),
        )
    else:
        raise ValueError(f"Unknown provider: {name}. Supported: {', '.join(SUPPORTED_PROVIDERS)}")
