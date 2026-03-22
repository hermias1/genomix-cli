import pytest
from genomix.agent.loop import AgentLoop
from genomix.providers.base import BaseProvider, ProviderResponse, ToolCall
from genomix.tools.registry import ToolRegistry


class MockProvider(BaseProvider):
    def __init__(self, responses):
        self._responses = list(responses)
        self._call_count = 0

    def chat(self, messages, tools=None):
        resp = self._responses[self._call_count]
        self._call_count += 1
        return resp

    def supports_tool_calling(self):
        return True

    def max_context_length(self):
        return 200_000


def test_simple_conversation():
    provider = MockProvider([ProviderResponse(content="The genome has 3 billion base pairs.")])
    registry = ToolRegistry()
    loop = AgentLoop(provider=provider, tool_registry=registry)
    response = loop.chat("How large is the human genome?")
    assert "3 billion" in response


def test_tool_call_loop():
    provider = MockProvider([
        ProviderResponse(content=None, tool_calls=[ToolCall(id="c1", name="count_reads", arguments={"path": "x.bam"})]),
        ProviderResponse(content="The file has 1000 reads."),
    ])
    registry = ToolRegistry()
    registry.register(name="count_reads", description="Count reads", parameters={"type": "object", "properties": {"path": {"type": "string"}}}, handler=lambda args: '{"count": 1000}')
    loop = AgentLoop(provider=provider, tool_registry=registry)
    response = loop.chat("How many reads in x.bam?")
    assert "1000" in response


def test_max_iterations_guard():
    infinite_tool_call = ProviderResponse(content=None, tool_calls=[ToolCall(id="c1", name="noop", arguments={})])
    provider = MockProvider([infinite_tool_call] * 50)
    registry = ToolRegistry()
    registry.register(name="noop", description="", parameters={"type": "object", "properties": {}}, handler=lambda args: "ok")
    loop = AgentLoop(provider=provider, tool_registry=registry, max_iterations=3)
    response = loop.chat("Do something")
    assert response  # Should return something, not hang


def test_forced_synthesis_on_last_round():
    provider = MockProvider([
        ProviderResponse(content=None, tool_calls=[ToolCall(id="c1", name="noop", arguments={})]),
        ProviderResponse(content=None, tool_calls=[ToolCall(id="c2", name="noop", arguments={})]),
        ProviderResponse(content="Final synthesis from gathered evidence."),
    ])
    registry = ToolRegistry()
    registry.register(name="noop", description="", parameters={"type": "object", "properties": {}}, handler=lambda args: "ok")
    loop = AgentLoop(provider=provider, tool_registry=registry, max_iterations=2)

    response = loop.chat("Summarize this")

    assert response == "Final synthesis from gathered evidence."
    assert provider._call_count == 3


def test_forced_synthesis_disables_tools():
    observed_tools = []

    class RecordingProvider(MockProvider):
        def chat(self, messages, tools=None):
            observed_tools.append(tools)
            return super().chat(messages, tools=tools)

    provider = RecordingProvider([
        ProviderResponse(content=None, tool_calls=[ToolCall(id="c1", name="noop", arguments={})]),
        ProviderResponse(content="Synthesis"),
    ])
    registry = ToolRegistry()
    registry.register(name="noop", description="", parameters={"type": "object", "properties": {}}, handler=lambda args: "ok")
    loop = AgentLoop(provider=provider, tool_registry=registry, max_iterations=1)

    response = loop.chat("Summarize this")

    assert response == "Synthesis"
    assert observed_tools[0] is not None
    assert observed_tools[-1] is None
