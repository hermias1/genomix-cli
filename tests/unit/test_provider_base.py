import pytest
from genomix.providers.base import BaseProvider, ToolCall, ProviderResponse
from genomix.providers import get_provider


def test_base_provider_is_abstract():
    with pytest.raises(TypeError):
        BaseProvider()


def test_provider_response_has_content_or_tool_calls():
    resp = ProviderResponse(content="Hello", tool_calls=[])
    assert resp.content == "Hello"
    assert resp.tool_calls == []


def test_tool_call_structure():
    tc = ToolCall(id="call_1", name="samtools_stats", arguments={"bam_path": "x.bam"})
    assert tc.name == "samtools_stats"
    assert tc.arguments["bam_path"] == "x.bam"


def test_get_provider_claude():
    from genomix.providers.claude import ClaudeProvider
    provider = get_provider("claude", api_key="test-key", model="claude-sonnet-4-6")
    assert isinstance(provider, ClaudeProvider)


def test_get_provider_unknown():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("unknown_provider")


def test_get_provider_openai():
    from genomix.providers.openai_provider import OpenAIProvider
    provider = get_provider("openai", api_key="test", model="gpt-4o")
    assert isinstance(provider, OpenAIProvider)


def test_get_provider_opencode():
    from genomix.providers.opencode import OpenCodeProvider
    provider = get_provider("opencode", endpoint="http://localhost:11434", model="llama3.3:70b")
    assert isinstance(provider, OpenCodeProvider)
