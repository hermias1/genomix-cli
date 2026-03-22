from unittest.mock import patch, MagicMock
from genomix.providers.opencode import OpenCodeProvider
from genomix.providers.claude import ClaudeProvider
from genomix.providers.openai_provider import OpenAIProvider
from genomix.providers.base import (
    StreamEvent, TextDelta, ToolCallStart, ToolCallArgs,
    ToolCallComplete, ToolResult, ErrorEvent, StreamDone,
)

def test_text_delta():
    e = TextDelta(text="hello")
    assert e.text == "hello"
    assert isinstance(e, StreamEvent)

def test_tool_call_start():
    e = ToolCallStart(id="c1", name="read_file")
    assert e.name == "read_file"

def test_tool_call_args():
    e = ToolCallArgs(id="c1", partial_args='{"path":')
    assert e.partial_args == '{"path":'

def test_tool_call_complete():
    e = ToolCallComplete(id="c1", name="read_file", arguments={"path": "x.vcf"})
    assert e.arguments["path"] == "x.vcf"

def test_tool_result():
    e = ToolResult(tool_name="read_file", result="contents...")
    assert e.tool_name == "read_file"

def test_error_event():
    e = ErrorEvent(message="timeout")
    assert e.message == "timeout"

def test_stream_done():
    e = StreamDone()
    assert isinstance(e, StreamEvent)


def _mock_sse_lines(chunks):
    import json
    lines = []
    for c in chunks:
        lines.append(f"data: {json.dumps(c)}")
    lines.append("data: [DONE]")
    return lines


def test_opencode_stream_text():
    chunks = [
        {"choices": [{"delta": {"content": "Hello"}, "finish_reason": None}]},
        {"choices": [{"delta": {"content": " world"}, "finish_reason": None}]},
    ]
    provider = OpenCodeProvider(model="test")
    mock_resp = MagicMock()
    mock_resp.iter_lines.return_value = iter(_mock_sse_lines(chunks))
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_client = MagicMock()
    mock_client.stream.return_value = mock_resp
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    with patch("httpx.Client", return_value=mock_client):
        events = list(provider.chat_stream([{"role": "user", "content": "hi"}]))
    text_events = [e for e in events if isinstance(e, TextDelta)]
    assert len(text_events) == 2
    assert text_events[0].text == "Hello"
    assert isinstance(events[-1], StreamDone)


def test_opencode_stream_tool_call():
    chunks = [
        {"choices": [{"delta": {"tool_calls": [{"index": 0, "id": "call_1", "function": {"name": "read_file", "arguments": ""}}]}, "finish_reason": None}]},
        {"choices": [{"delta": {"tool_calls": [{"index": 0, "function": {"arguments": '{"path":"x.vcf"}'}}]}, "finish_reason": None}]},
    ]
    provider = OpenCodeProvider(model="test")
    mock_resp = MagicMock()
    mock_resp.iter_lines.return_value = iter(_mock_sse_lines(chunks))
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_client = MagicMock()
    mock_client.stream.return_value = mock_resp
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    with patch("httpx.Client", return_value=mock_client):
        events = list(provider.chat_stream([{"role": "user", "content": "read"}]))
    starts = [e for e in events if isinstance(e, ToolCallStart)]
    args = [e for e in events if isinstance(e, ToolCallArgs)]
    assert len(starts) == 1
    assert starts[0].name == "read_file"
    assert starts[0].id == "call_1"
    assert len(args) == 1


def test_claude_has_chat_stream():
    provider = ClaudeProvider(api_key="test")
    assert hasattr(provider, "chat_stream")
    assert callable(provider.chat_stream)


def test_openai_has_chat_stream():
    provider = OpenAIProvider(api_key="test")
    assert hasattr(provider, "chat_stream")
    assert callable(provider.chat_stream)


# --- AgentLoop streaming tests ---

from genomix.agent.loop import AgentLoop
from genomix.providers.base import BaseProvider, ProviderResponse
from genomix.tools.registry import ToolRegistry


class MockStreamProvider(BaseProvider):
    def __init__(self, event_sequences):
        self._sequences = list(event_sequences)
        self._call = 0

    def chat(self, messages, tools=None):
        return ProviderResponse(content="fallback")

    def chat_stream(self, messages, tools=None):
        events = self._sequences[self._call]
        self._call += 1
        yield from events

    def supports_tool_calling(self):
        return True

    def max_context_length(self):
        return 200_000


def test_agent_stream_simple_text():
    provider = MockStreamProvider([[
        TextDelta(text="Hello "),
        TextDelta(text="world"),
        StreamDone(),
    ]])
    loop = AgentLoop(provider=provider, tool_registry=ToolRegistry())
    events = list(loop.chat_stream("hi"))
    texts = [e for e in events if isinstance(e, TextDelta)]
    assert len(texts) == 2
    assert texts[0].text == "Hello "
    assert any(isinstance(e, StreamDone) for e in events)


def test_agent_stream_tool_call():
    provider = MockStreamProvider([
        [
            ToolCallStart(id="c1", name="echo"),
            ToolCallArgs(id="c1", partial_args='{"text":'),
            ToolCallArgs(id="c1", partial_args='"hello"}'),
            StreamDone(),
        ],
        [
            TextDelta(text="echoed: hello"),
            StreamDone(),
        ],
    ])
    registry = ToolRegistry()
    registry.register(
        name="echo", description="Echo",
        parameters={"type": "object", "properties": {"text": {"type": "string"}}},
        handler=lambda args: f"echo: {args['text']}",
    )
    loop = AgentLoop(provider=provider, tool_registry=registry)
    events = list(loop.chat_stream("echo hello"))
    completes = [e for e in events if isinstance(e, ToolCallComplete)]
    results = [e for e in events if isinstance(e, ToolResult)]
    texts = [e for e in events if isinstance(e, TextDelta)]
    assert len(completes) == 1
    assert completes[0].arguments == {"text": "hello"}
    assert len(results) == 1
    assert len(texts) >= 1


def test_agent_chat_uses_stream():
    provider = MockStreamProvider([[
        TextDelta(text="result"),
        StreamDone(),
    ]])
    loop = AgentLoop(provider=provider, tool_registry=ToolRegistry())
    result = loop.chat("hi")
    assert result == "result"


# --- StreamingRenderer tests ---

from io import StringIO
from rich.console import Console
from genomix.tui_renderer import StreamingRenderer


def test_renderer_text_delta():
    console = Console(file=StringIO(), force_terminal=True)
    renderer = StreamingRenderer(console)
    renderer.handle_event(TextDelta(text="Hello"))
    renderer.handle_event(TextDelta(text=" world"))
    renderer.handle_event(StreamDone())
    output = console.file.getvalue()
    assert "Hello" in output
    assert "world" in output


def test_renderer_tool_call():
    console = Console(file=StringIO(), force_terminal=True)
    renderer = StreamingRenderer(console)
    renderer.handle_event(ToolCallStart(id="c1", name="read_file"))
    renderer.handle_event(ToolCallComplete(id="c1", name="read_file", arguments={"path": "x.vcf"}))
    renderer.handle_event(ToolResult(tool_name="read_file", result="file contents here"))
    output = console.file.getvalue()
    assert "read_file" in output


def test_renderer_paragraph_detection():
    console = Console(file=StringIO(), force_terminal=True)
    renderer = StreamingRenderer(console)
    renderer.handle_event(TextDelta(text="Para one.\n\n"))
    renderer.handle_event(TextDelta(text="Para two."))
    renderer.handle_event(StreamDone())
    output = console.file.getvalue()
    assert "Para one" in output
    assert "Para two" in output
