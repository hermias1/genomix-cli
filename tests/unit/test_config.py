import os
from pathlib import Path

import pytest
import yaml

from genomix.config import GenomixConfig, load_config, load_secrets, save_secrets


def test_default_config():
    config = GenomixConfig()
    assert config.provider == "ollama"
    assert config.model == "qwen3-coder:30b"
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
    assert config.provider == "ollama"


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


import stat

def test_save_secrets_sets_permissions(tmp_path):
    path = tmp_path / "secrets.yaml"
    save_secrets({"key": "value"}, secrets_path=path)
    mode = oct(stat.S_IMODE(os.stat(path).st_mode))
    assert mode == "0o600"


def test_save_config_round_trip(tmp_path):
    from genomix.config import save_config

    path = tmp_path / "config.yaml"
    save_config(
        GenomixConfig(
            provider="openai",
            model="gpt-4o",
            max_concurrent_swarm=2,
            mcp_servers={"ncbi": {"enabled": True}},
            privacy_mode=True,
        ),
        config_path=path,
    )

    loaded = load_config(config_path=path)
    assert loaded.provider == "openai"
    assert loaded.model == "gpt-4o"
    assert loaded.max_concurrent_swarm == 2
    assert loaded.mcp_servers["ncbi"]["enabled"] is True
    assert loaded.privacy_mode is True


def test_is_local_true_for_default_ollama():
    assert GenomixConfig(provider="ollama").is_local() is True


def test_is_local_false_for_remote_ollama_endpoint():
    config = GenomixConfig(provider="ollama", endpoint="https://ollama.example.org")
    assert config.is_local() is False


def test_is_local_true_for_loopback_ollama_endpoint():
    config = GenomixConfig(provider="ollama", endpoint="http://127.0.0.1:11434")
    assert config.is_local() is True
