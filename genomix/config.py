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
    provider: str = "claude"
    model: str = "claude-sonnet-4-6"
    max_concurrent_swarm: int = 4
    mcp_servers: dict[str, dict[str, Any]] = field(default_factory=dict)
    privacy_mode: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GenomixConfig:
        provider_data = data.get("provider", {})
        return cls(
            provider=provider_data.get("default", "claude"),
            model=provider_data.get("model", "claude-sonnet-4-6"),
            max_concurrent_swarm=data.get("max_concurrent_swarm", 4),
            mcp_servers=data.get("mcp_servers", {}),
            privacy_mode=data.get("privacy_mode", False),
        )


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
