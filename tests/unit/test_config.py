import os
from pathlib import Path

import pytest
import yaml

from genomix.config import GenomixConfig, load_config, load_secrets


def test_default_config():
    config = GenomixConfig()
    assert config.provider == "claude"
    assert config.model == "claude-sonnet-4-6"
    assert config.max_concurrent_swarm == 4


def test_load_config_from_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "provider": {"default": "openai", "model": "gpt-4o"},
    }))
    config = load_config(config_path=config_file)
    assert config.provider == "openai"
    assert config.model == "gpt-4o"
    assert config.max_concurrent_swarm == 4


def test_load_config_missing_file():
    config = load_config(config_path=Path("/nonexistent/config.yaml"))
    assert config.provider == "claude"


def test_load_secrets(tmp_path):
    secrets_file = tmp_path / "secrets.yaml"
    secrets_file.write_text(yaml.dump({
        "anthropic_api_key": "sk-ant-test",
        "ncbi_api_key": "ncbi123",
    }))
    secrets = load_secrets(secrets_path=secrets_file)
    assert secrets["anthropic_api_key"] == "sk-ant-test"
    assert secrets["ncbi_api_key"] == "ncbi123"


def test_load_secrets_missing_file():
    secrets = load_secrets(secrets_path=Path("/nonexistent/secrets.yaml"))
    assert secrets == {}


def test_config_mcp_servers(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "mcp_servers": {
            "samtools": {"enabled": True, "binary_path": "/usr/bin/samtools"},
            "cosmic": {"enabled": False},
        },
    }))
    config = load_config(config_path=config_file)
    assert config.mcp_servers["samtools"]["enabled"] is True
    assert config.mcp_servers["samtools"]["binary_path"] == "/usr/bin/samtools"
    assert config.mcp_servers["cosmic"]["enabled"] is False
