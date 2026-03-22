# Streaming Responses Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace spinner+full-response with real-time token-by-token streaming, paragraph-by-paragraph markdown rendering, and live tool call display across all 3 providers.

**Architecture:** Typed `StreamEvent` dataclasses flow from provider → agent loop → TUI renderer. Providers yield SSE chunks as events, the agent loop handles tool call accumulation and dispatch, the renderer displays text progressively with Rich Live.

**Tech Stack:** Python generators, httpx streaming, anthropic SDK streaming, openai SDK streaming, Rich Live

**Spec:** `docs/superpowers/specs/2026-03-22-streaming-design.md`

---

## File Structure

```
genomix/
├── providers/
│   ├── base.py              # Add StreamEvent types + chat_stream() ABC
│   ├── opencode.py          # Implement chat_stream() with httpx SSE
│   ├── claude.py            # Implement chat_stream() with Anthropic SDK
│   └── openai_provider.py   # Implement chat_stream() with OpenAI SDK
├── agent/
│   └── loop.py              # Add chat_stream() generator, refactor chat()
├── tui.py                   # Replace spinner with StreamingRenderer
└── tui_renderer.py          # NEW: StreamingRenderer with Rich Live

tests/unit/
└── test_streaming.py        # NEW: all streaming tests
```

---

## Task 1: Stream Event Types

**Files:**
- Modify: `genomix/providers/base.py`
- Create: `tests/unit/test_streaming.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_streaming.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `source .venv/bin/activate && python -m pytest tests/unit/test_streaming.py -v`
Expected: FAIL — `cannot import name 'StreamEvent'`

- [ ] **Step 3: Add event types to base.py**

Add to `genomix/providers/base.py` (keep existing `BaseProvider`, `ToolCall`, `ProviderResponse` untouched):

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generator


# --- Stream Event Types ---

class StreamEvent:
    """Base class for streaming events."""
    pass


@dataclass
class TextDelta(StreamEvent):
    text: str


@dataclass
class ToolCallStart(StreamEvent):
    id: str
    name: str


@dataclass
class ToolCallArgs(StreamEvent):
    id: str
    partial_args: str


@dataclass
class ToolCallComplete(StreamEvent):
    id: str
    name: str
    arguments: dict


@dataclass
class ToolResult(StreamEvent):
    tool_name: str
    result: str


@dataclass
class ErrorEvent(StreamEvent):
    message: str


@dataclass
class StreamDone(StreamEvent):
    pass


# --- Existing types (keep as-is) ---

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ProviderResponse:
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


# --- Provider ABC ---

class BaseProvider(ABC):
    @abstractmethod
    def chat(self, messages, tools=None) -> ProviderResponse:
        ...

    @abstractmethod
    def chat_stream(self, messages, tools=None) -> Generator[StreamEvent, None, None]:
        ...

    @abstractmethod
    def supports_tool_calling(self) -> bool:
        ...

    @abstractmethod
    def max_context_length(self) -> int:
        ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_streaming.py -v`
Expected: 7 PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/providers/base.py tests/unit/test_streaming.py
git commit -m "feat: add StreamEvent types for streaming responses"
```

---

## Task 2: OpenCode Provider Streaming (Ollama)

**Files:**
- Modify: `genomix/providers/opencode.py`
- Modify: `tests/unit/test_streaming.py` (add tests)

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/test_streaming.py`:
```python
from unittest.mock import patch, MagicMock
from genomix.providers.opencode import OpenCodeProvider


def _mock_sse_lines(chunks):
    """Create mock SSE response lines from chunk dicts."""
    import json
    lines = []
    for c in chunks:
        lines.append(f"data: {json.dumps(c)}")
    lines.append("data: [DONE]")
    return lines


def test_opencode_stream_text():
    """Streaming yields TextDelta events for text content."""
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
    assert text_events[1].text == " world"
    assert isinstance(events[-1], StreamDone)


def test_opencode_stream_tool_call():
    """Streaming yields ToolCallStart + ToolCallArgs for tool calls."""
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
        events = list(provider.chat_stream([{"role": "user", "content": "read x.vcf"}]))

    starts = [e for e in events if isinstance(e, ToolCallStart)]
    args = [e for e in events if isinstance(e, ToolCallArgs)]
    assert len(starts) == 1
    assert starts[0].name == "read_file"
    assert starts[0].id == "call_1"
    assert len(args) == 1
    assert '"path"' in args[0].partial_args
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_streaming.py::test_opencode_stream_text -v`
Expected: FAIL — `OpenCodeProvider has no attribute 'chat_stream'`

- [ ] **Step 3: Implement chat_stream in opencode.py**

Add `chat_stream()` method and `_clean_messages()` helper to `OpenCodeProvider`. Follow the spec exactly (Section 3, OpenCodeProvider). Keep existing `chat()` method unchanged.

```python
def _clean_messages(self, messages):
    clean = []
    for m in messages:
        msg = {k: v for k, v in m.items() if k in ("role", "content", "tool_call_id", "tool_calls")}
        if msg.get("content") is None:
            msg["content"] = ""
        clean.append(msg)
    return clean

def chat_stream(self, messages, tools=None):
    from genomix.providers.base import TextDelta, ToolCallStart, ToolCallArgs, StreamDone
    clean_messages = self._clean_messages(messages)
    payload = {"model": self.model, "messages": clean_messages, "stream": True}
    if tools:
        payload["tools"] = tools
    current_tool_ids = {}

    with httpx.Client(timeout=300) as client:
        with client.stream("POST", f"{self.endpoint}/v1/chat/completions", json=payload) as resp:
            for line in resp.iter_lines():
                if not line.startswith("data: "):
                    continue
                if line == "data: [DONE]":
                    yield StreamDone()
                    return
                chunk = json.loads(line[6:])
                delta = chunk["choices"][0]["delta"]
                if delta.get("content"):
                    yield TextDelta(text=delta["content"])
                if delta.get("tool_calls"):
                    for tc in delta["tool_calls"]:
                        idx = tc.get("index", 0)
                        if tc.get("id"):
                            current_tool_ids[idx] = tc["id"]
                        tc_id = current_tool_ids.get(idx, f"call_{idx}")
                        if tc.get("function", {}).get("name"):
                            yield ToolCallStart(id=tc_id, name=tc["function"]["name"])
                        if tc.get("function", {}).get("arguments"):
                            yield ToolCallArgs(id=tc_id, partial_args=tc["function"]["arguments"])
    yield StreamDone()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_streaming.py -v`
Expected: 9 PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/providers/opencode.py tests/unit/test_streaming.py
git commit -m "feat: add streaming to OpenCode/Ollama provider"
```

---

## Task 3: Claude Provider Streaming

**Files:**
- Modify: `genomix/providers/claude.py`
- Modify: `tests/unit/test_streaming.py` (add tests)

- [ ] **Step 1: Write failing test**

Add to `tests/unit/test_streaming.py`:
```python
from genomix.providers.claude import ClaudeProvider


def test_claude_has_chat_stream():
    """ClaudeProvider has a chat_stream method."""
    provider = ClaudeProvider(api_key="test")
    assert hasattr(provider, "chat_stream")
    assert callable(provider.chat_stream)
```

- [ ] **Step 2: Implement chat_stream in claude.py**

Add `chat_stream()` to `ClaudeProvider`. Use `self.client.messages.stream()` context manager. Track `current_block_id` for tool call deltas. Yield `StreamDone` on `message_stop` + safety yield after the `with` block. Reuse existing `_convert_tool()` for tool schema conversion.

- [ ] **Step 3: Run tests, verify pass**

Run: `python -m pytest tests/unit/test_streaming.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add genomix/providers/claude.py tests/unit/test_streaming.py
git commit -m "feat: add streaming to Claude/Anthropic provider"
```

---

## Task 4: OpenAI Provider Streaming

**Files:**
- Modify: `genomix/providers/openai_provider.py`
- Modify: `tests/unit/test_streaming.py` (add test)

- [ ] **Step 1: Write failing test**

Add to `tests/unit/test_streaming.py`:
```python
from genomix.providers.openai_provider import OpenAIProvider


def test_openai_has_chat_stream():
    """OpenAIProvider has a chat_stream method."""
    provider = OpenAIProvider(api_key="test")
    assert hasattr(provider, "chat_stream")
    assert callable(provider.chat_stream)
```

- [ ] **Step 2: Implement chat_stream in openai_provider.py**

Add `chat_stream()` to `OpenAIProvider`. Use `self.client.chat.completions.create(stream=True)`. Track `current_tool_ids` by index. Yield `StreamDone` on `finish_reason in ("stop", "tool_calls")` + safety yield.

- [ ] **Step 3: Run tests, verify pass**

- [ ] **Step 4: Commit**

```bash
git add genomix/providers/openai_provider.py tests/unit/test_streaming.py
git commit -m "feat: add streaming to OpenAI provider"
```

---

## Task 5: Agent Loop Streaming

**Files:**
- Modify: `genomix/agent/loop.py`
- Modify: `tests/unit/test_streaming.py` (add tests)

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/test_streaming.py`:
```python
from genomix.agent.loop import AgentLoop
from genomix.providers.base import BaseProvider, ProviderResponse, StreamDone, TextDelta, ToolCallStart, ToolCallArgs
from genomix.tools.registry import ToolRegistry


class MockStreamProvider(BaseProvider):
    """Provider that yields canned stream events."""
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
    """Agent streams text events through."""
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
    """Agent accumulates tool call args and dispatches tool."""
    provider = MockStreamProvider([
        # First call: LLM wants to call a tool
        [
            ToolCallStart(id="c1", name="echo"),
            ToolCallArgs(id="c1", partial_args='{"text":'),
            ToolCallArgs(id="c1", partial_args='"hello"}'),
            StreamDone(),
        ],
        # Second call: LLM responds with text
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

    from genomix.providers.base import ToolCallComplete, ToolResult
    completes = [e for e in events if isinstance(e, ToolCallComplete)]
    results = [e for e in events if isinstance(e, ToolResult)]
    texts = [e for e in events if isinstance(e, TextDelta)]
    assert len(completes) == 1
    assert completes[0].arguments == {"text": "hello"}
    assert len(results) == 1
    assert len(texts) >= 1


def test_agent_chat_uses_stream():
    """Non-streaming chat() works via chat_stream() internally."""
    provider = MockStreamProvider([[
        TextDelta(text="result"),
        StreamDone(),
    ]])
    loop = AgentLoop(provider=provider, tool_registry=ToolRegistry())
    result = loop.chat("hi")
    assert result == "result"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_streaming.py::test_agent_stream_simple_text -v`
Expected: FAIL — `AgentLoop has no attribute 'chat_stream'`

- [ ] **Step 3: Implement chat_stream in loop.py**

Rewrite `genomix/agent/loop.py`:
- Add `chat_stream()` generator method per spec Section 4
- Refactor `chat()` to consume `chat_stream()` (just accumulates TextDelta)
- Keep `_build_messages()` with context compression
- Add `_force_final_synthesis_stream()` per spec
- Remove callback invocations (`on_tool_call`, `on_tool_result`, `on_thinking`) — they are deprecated (keep params in `__init__` for compat but don't call them)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_streaming.py -v`
Expected: All PASS

- [ ] **Step 5: Run full test suite to check backward compat**

Run: `python -m pytest tests/ -v`
Expected: All existing tests PASS (chat() still works)

- [ ] **Step 6: Commit**

```bash
git add genomix/agent/loop.py tests/unit/test_streaming.py
git commit -m "feat: add streaming to agent loop with tool call accumulation"
```

---

## Task 6: Streaming Renderer

**Files:**
- Create: `genomix/tui_renderer.py`
- Modify: `tests/unit/test_streaming.py` (add tests)

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/test_streaming.py`:
```python
from io import StringIO
from rich.console import Console
from genomix.tui_renderer import StreamingRenderer


def test_renderer_text_delta():
    """Renderer outputs text from TextDelta events."""
    console = Console(file=StringIO(), force_terminal=True)
    renderer = StreamingRenderer(console)
    renderer.handle_event(TextDelta(text="Hello"))
    renderer.handle_event(TextDelta(text=" world"))
    renderer.handle_event(StreamDone())
    output = console.file.getvalue()
    assert "Hello" in output
    assert "world" in output


def test_renderer_tool_call():
    """Renderer shows tool call with ⚡ icon."""
    console = Console(file=StringIO(), force_terminal=True)
    renderer = StreamingRenderer(console)
    renderer.handle_event(ToolCallStart(id="c1", name="read_file"))
    from genomix.providers.base import ToolCallComplete, ToolResult
    renderer.handle_event(ToolCallComplete(id="c1", name="read_file", arguments={"path": "x.vcf"}))
    renderer.handle_event(ToolResult(tool_name="read_file", result="file contents..."))
    output = console.file.getvalue()
    assert "read_file" in output


def test_renderer_paragraph_detection():
    """Renderer detects paragraph boundaries on double newline."""
    console = Console(file=StringIO(), force_terminal=True)
    renderer = StreamingRenderer(console)
    renderer.handle_event(TextDelta(text="Paragraph one.\n\n"))
    renderer.handle_event(TextDelta(text="Paragraph two."))
    renderer.handle_event(StreamDone())
    # Both paragraphs should be in output
    output = console.file.getvalue()
    assert "Paragraph one" in output
    assert "Paragraph two" in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_streaming.py::test_renderer_text_delta -v`
Expected: FAIL — `No module named 'genomix.tui_renderer'`

- [ ] **Step 3: Implement StreamingRenderer**

Create `genomix/tui_renderer.py`:

```python
"""Streaming renderer — displays LLM responses progressively with Rich."""
from __future__ import annotations

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

from genomix.providers.base import (
    StreamEvent, TextDelta, ToolCallStart, ToolCallComplete,
    ToolResult, ErrorEvent, StreamDone,
)


class StreamingRenderer:
    """Renders streaming events to terminal, paragraph-by-paragraph."""

    def __init__(self, console: Console):
        self.console = console
        self._buffer = ""
        self._finalized_text = ""
        self._live: Live | None = None

    def handle_event(self, event: StreamEvent) -> None:
        if isinstance(event, TextDelta):
            self._buffer += event.text

            # Check for paragraph boundary
            if "\n\n" in self._buffer:
                parts = self._buffer.split("\n\n", 1)
                self._finalized_text += parts[0] + "\n\n"
                self._buffer = parts[1]

            self._update_live()

        elif isinstance(event, ToolCallStart):
            self._stop_live()
            self.console.print(f"  [dim #00d787]⚡ {event.name}[/]", end="")

        elif isinstance(event, ToolCallComplete):
            args_str = ", ".join(f"{k}={v!r}" for k, v in list(event.arguments.items())[:3])
            if len(args_str) > 50:
                args_str = args_str[:47] + "..."
            self.console.print(f"([dim]{args_str}[/])")

        elif isinstance(event, ToolResult):
            preview = event.result.replace("\n", " ")[:80]
            self.console.print(f"  [dim]  ↳ {preview}[/]")

        elif isinstance(event, ErrorEvent):
            self._stop_live()
            self.console.print(f"\n[red]Error: {event.message}[/]")

        elif isinstance(event, StreamDone):
            self._finalized_text += self._buffer
            self._buffer = ""
            self._stop_live()
            # Final render as Markdown
            if self._finalized_text.strip():
                self.console.print()
                self.console.print(Markdown(self._finalized_text.strip()))
            self.console.print()

    def _update_live(self) -> None:
        """Update the live display with current streaming text."""
        display_text = self._finalized_text + self._buffer
        if not display_text.strip():
            return
        if self._live is None:
            self._live = Live(
                Text(display_text),
                console=self.console,
                refresh_per_second=10,
            )
            self._live.start()
        else:
            self._live.update(Text(display_text))

    def _stop_live(self) -> None:
        """Stop the live display."""
        if self._live is not None:
            self._live.stop()
            self._live = None
            # Clear the live output — final Markdown will be printed on StreamDone
            # (Rich Live cleans up its own output on stop)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_streaming.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/tui_renderer.py tests/unit/test_streaming.py
git commit -m "feat: add StreamingRenderer with Rich Live"
```

---

## Task 7: Wire TUI to Streaming

**Files:**
- Modify: `genomix/tui.py`

- [ ] **Step 1: Modify _run_agent in tui.py**

Read the current `genomix/tui.py` first. In `_run_agent()`, replace the spinner+chat pattern with streaming:

```python
def _run_agent(self, message, skill_path=None):
    try:
        from genomix.runtime import iteration_budget_for
        from genomix.tui_renderer import StreamingRenderer

        max_iterations = iteration_budget_for(message, skill_path=skill_path)
        if skill_path or self.agent_loop is None:
            loop = self._create_agent_loop(skill_path=skill_path, max_iterations=max_iterations)
            if not skill_path:
                self.agent_loop = loop
        else:
            loop = self.agent_loop
            loop.max_iterations = max_iterations

        # Stream response
        self.console.print()
        renderer = StreamingRenderer(self.console)
        start_index = len(loop.messages)
        for event in loop.chat_stream(message):
            renderer.handle_event(event)

        # Save session
        if self.project:
            from genomix.agent.session_store import SessionStore
            title = (message.splitlines()[0][:80] or "Session").strip()
            store = SessionStore(self.project.root / ".genomix" / "runtime" / "sessions.db")
            store.save_session(loop.messages[start_index:], title=title)

    except KeyboardInterrupt:
        self.console.print("\n[dim]Interrupted.[/]\n")
    except Exception as e:
        self.console.print(f"\n[red]Error: {e}[/]\n")
```

- [ ] **Step 2: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Manual smoke test**

Run: `source .venv/bin/activate && cd /tmp/genomix_test && python -m genomix.cli`
Type: `Read tiny.fasta and summarize`
Expected: Text streams token by token, tool call appears with ⚡, final response rendered as Markdown

- [ ] **Step 4: Commit**

```bash
git add genomix/tui.py
git commit -m "feat: wire streaming renderer into interactive TUI"
```

---

## Task 8: Full Integration Test + Push

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Test backward compatibility**

Run: `python -m genomix.cli ask "What is BRCA1?" 2>&1 | head -5`
Expected: Non-streaming mode still works, returns text

- [ ] **Step 3: Commit and push**

```bash
git push origin main
```

- [ ] **Step 4: Tag v0.2.0-alpha**

```bash
git tag v0.2.0-alpha
git push origin v0.2.0-alpha
```
