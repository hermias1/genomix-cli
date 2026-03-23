"""Configuration loading for Genomix CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

GENOMIX_HOME = Path(os.environ.get("GENOMIX_HOME", Path.home() / ".genomix"))


@dataclass
class GenomixConfig:
    provider: str = "ollama"
    model: str = "qwen3-coder:30b"
    endpoint: str = ""  # Custom endpoint (e.g. remote Ollama)
    max_concurrent_swarm: int = 4
    mcp_servers: dict[str, dict[str, Any]] = field(default_factory=dict)
    privacy_mode: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GenomixConfig:
        provider_data = data.get("provider", {})
        return cls(
            provider=provider_data.get("default", "ollama"),
            model=provider_data.get("model", "qwen3-coder:30b"),
            endpoint=provider_data.get("endpoint", ""),
            max_concurrent_swarm=data.get("max_concurrent_swarm", 4),
            mcp_servers=data.get("mcp_servers", {}),
            privacy_mode=data.get("privacy_mode", False),
        )

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "provider": {
                "default": self.provider,
                "model": self.model,
            },
            "max_concurrent_swarm": self.max_concurrent_swarm,
            "mcp_servers": self.mcp_servers,
            "privacy_mode": self.privacy_mode,
        }
        if self.endpoint:
            d["provider"]["endpoint"] = self.endpoint
        return d

    def is_local(self) -> bool:
        """Check if the current provider runs locally (no data sent to cloud)."""
        if self.provider in ("claude", "openai"):
            return False
        if self.provider == "opencode" and self.endpoint:
            from urllib.parse import urlparse
            host = urlparse(self.endpoint).hostname or ""
            return host in ("localhost", "127.0.0.1", "0.0.0.0", "::1")
        # Default opencode with no endpoint = localhost
        return self.provider == "opencode"


def load_config(config_path: Path | None = None) -> GenomixConfig:
    if config_path is None:
        config_path = GENOMIX_HOME / "config.yaml"
    if not config_path.exists():
        return GenomixConfig()
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}
    return GenomixConfig.from_dict(data)


def load_secrets(secrets_path: Path | None = None) -> dict[str, str]:
    if secrets_path is None:
        secrets_path = GENOMIX_HOME / "secrets.yaml"
    if not secrets_path.exists():
        return {}
    with open(secrets_path) as f:
        data = yaml.safe_load(f) or {}
    return data


def save_secrets(data, secrets_path=None):
    if secrets_path is None:
        secrets_path = GENOMIX_HOME / "secrets.yaml"
    secrets_path.parent.mkdir(parents=True, exist_ok=True)
    with open(secrets_path, "w") as f:
        yaml.dump(data, f)
    os.chmod(secrets_path, 0o600)


def save_config(config: GenomixConfig, config_path: Path | None = None) -> None:
    if config_path is None:
        config_path = GENOMIX_HOME / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(config.to_dict(), f, sort_keys=False)
