import pytest

from genomix.providers.opencode import OpenCodeProvider, _default_timeout_seconds


def test_default_timeout_is_extended(monkeypatch):
    monkeypatch.delenv("GENOMIX_OLLAMA_TIMEOUT_SECONDS", raising=False)
    assert _default_timeout_seconds() == 900.0


def test_timeout_reads_from_env(monkeypatch):
    monkeypatch.setenv("GENOMIX_OLLAMA_TIMEOUT_SECONDS", "1200")
    assert _default_timeout_seconds() == 1200.0


def test_invalid_timeout_env_falls_back(monkeypatch):
    monkeypatch.setenv("GENOMIX_OLLAMA_TIMEOUT_SECONDS", "bad")
    assert _default_timeout_seconds() == 900.0


def test_provider_uses_override_timeout():
    provider = OpenCodeProvider(timeout_seconds=42)
    timeout = provider._http_timeout()
    assert timeout.connect == 10.0
    assert timeout.read == 42
    assert timeout.write == 42
