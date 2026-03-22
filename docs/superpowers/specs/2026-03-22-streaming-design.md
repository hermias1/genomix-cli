# Genomix CLI v0.2.0 — Streaming Responses Design Specification

**Date:** 2026-03-22
**Status:** Approved
**Scope:** Streaming for all 3 providers (Ollama, Claude, OpenAI) + agent loop + TUI renderer

---

## 1. Goal

Replace the current "spinner → full response" pattern with real-time token-by-token streaming. Text flows as it's generated, tool calls appear immediately, and markdown is rendered paragraph-by-paragraph. All 3 providers support streaming.

## 2. Stream Event Types

All streaming communication uses typed events defined in `genomix/providers/base.py`:

```python
from dataclasses import dataclass

class StreamEvent:
    """Base class for streaming events."""
    pass

@dataclass
class TextDelta(StreamEvent):
    """A fragment of text from the LLM."""
    text: str

@dataclass
class ToolCallStart(StreamEvent):
    """The LLM begins a tool call."""
    id: str
    name: str

@dataclass
class ToolCallArgs(StreamEvent):
    """Partial JSON arguments for a tool call (streamed incrementally)."""
    id: str
    partial_args: str

@dataclass
class ToolCallComplete(StreamEvent):
    """A tool call's arguments are fully received and parsed."""
    id: str
    name: str
    arguments: dict

@dataclass
class ToolResult(StreamEvent):
    """Result from an executed tool call (preview for TUI display)."""
    tool_name: str
    result: str  # First 200 chars

@dataclass
class ErrorEvent(StreamEvent):
    """An error occurred during streaming."""
    message: str

@dataclass
class StreamDone(StreamEvent):
    """The LLM has finished its response (no more events)."""
    pass
```

Note: `ToolCallArgs` is internal to the provider→agent loop communication. It is never yielded to the TUI. The TUI only sees: `ToolCallStart`, `ToolCallComplete`, `ToolResult`, `TextDelta`, `ErrorEvent`, `StreamDone`.

## 3. Provider Streaming Interface

### BaseProvider changes

Add `chat_stream()` as a generator method alongside existing `chat()`:

```python
class BaseProvider(ABC):
    @abstractmethod
    def chat(self, messages, tools=None) -> ProviderResponse:
        """Non-streaming: returns complete response."""
        ...

    @abstractmethod
    def chat_stream(self, messages, tools=None) -> Generator[StreamEvent, None, None]:
        """Streaming: yields StreamEvents as they arrive."""
        ...
```

### OpenCodeProvider (Ollama)

```python
def chat_stream(self, messages, tools=None):
    clean_messages = self._clean_messages(messages)  # ensure content is str, not None
    payload = {"model": self.model, "messages": clean_messages, "stream": True}
    if tools:
        payload["tools"] = tools
    current_tool_ids = {}  # index -> id (Ollama only sends id on first chunk per tool)

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

                # Text content
                if delta.get("content"):
                    yield TextDelta(text=delta["content"])

                # Tool calls (track id by index, same pattern as OpenAI)
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
    yield StreamDone()  # Safety: stream ended without [DONE] sentinel
```

The provider tracks the current tool call id by index. Ollama, like OpenAI, only includes the `id` field on the first chunk of a tool call. The provider must store `current_tool_id` from `ToolCallStart` and reuse it for subsequent `ToolCallArgs` events.

The agent loop (not the provider) is responsible for accumulating `ToolCallArgs` into complete arguments and yielding `ToolCallComplete`. Tool call completion is detected when `StreamDone` is received. The provider MUST always yield `StreamDone` at the end — if the HTTP stream ends without the `[DONE]` sentinel, yield `StreamDone` after exiting the loop.

### ClaudeProvider (Anthropic SDK)

```python
def chat_stream(self, messages, tools=None):
    kwargs = self._build_request(messages, tools)  # reuse existing request builder
    current_block_id = None  # Track content block id across delta events

    with self.client.messages.stream(**kwargs) as stream:
        for event in stream:
            if event.type == "content_block_start":
                if event.content_block.type == "tool_use":
                    current_block_id = event.content_block.id
                    yield ToolCallStart(id=current_block_id, name=event.content_block.name)
                elif event.content_block.type == "text":
                    current_block_id = None
            elif event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    yield TextDelta(text=event.delta.text)
                elif event.delta.type == "input_json_delta":
                    yield ToolCallArgs(id=current_block_id, partial_args=event.delta.partial_json)
            elif event.type == "message_stop":
                yield StreamDone()
    # Safety: always yield StreamDone if stream ends without message_stop
    yield StreamDone()
```

### OpenAIProvider

```python
def chat_stream(self, messages, tools=None):
    stream = self.client.chat.completions.create(model=self.model, messages=messages, tools=tools, stream=True)
    current_tool_ids = {}  # index -> id (OpenAI only sends id on first chunk per tool)

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield TextDelta(text=delta.content)
        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if tc.id:
                    current_tool_ids[idx] = tc.id
                tc_id = current_tool_ids.get(idx, f"call_{idx}")
                if tc.function and tc.function.name:
                    yield ToolCallStart(id=tc_id, name=tc.function.name)
                if tc.function and tc.function.arguments:
                    yield ToolCallArgs(id=tc_id, partial_args=tc.function.arguments)
        if chunk.choices[0].finish_reason in ("stop", "tool_calls"):
            yield StreamDone()
            return
    yield StreamDone()  # Safety: stream ended without finish_reason
```

## 4. Agent Loop Streaming

### New `chat_stream()` method

`AgentLoop.chat_stream(user_message)` is a generator that:

1. Appends user message to conversation history
2. Calls `provider.chat_stream()` and yields events to the caller
3. When tool calls are detected:
   - Accumulates `ToolCallArgs` into complete JSON
   - When complete: yields `ToolCallComplete`, dispatches the tool, yields the result
   - Calls `provider.chat_stream()` again with the tool result (loops back)
4. When text is received: yields `TextDelta` directly
5. Stores the complete response in conversation history
6. Applies context compression between iterations if needed

```python
def chat_stream(self, user_message: str) -> Generator[StreamEvent, None, None]:
    self.messages.append({"role": "user", "content": user_message})
    tools = self.tool_registry.list_tools() or None

    for iteration in range(self.max_iterations):
        all_messages = self._build_messages()

        accumulated_text = ""
        pending_tool_calls = {}  # id -> {name, args_buffer}

        for event in self.provider.chat_stream(all_messages, tools=tools):
            if isinstance(event, TextDelta):
                accumulated_text += event.text
                yield event

            elif isinstance(event, ToolCallStart):
                pending_tool_calls[event.id] = {"name": event.name, "args": ""}
                yield event

            elif isinstance(event, ToolCallArgs):
                if event.id in pending_tool_calls:
                    pending_tool_calls[event.id]["args"] += event.partial_args

            elif isinstance(event, StreamDone):
                break

        # If we have tool calls, execute them
        if pending_tool_calls:
            # Store assistant message with tool calls
            tool_calls_msg = [...]
            self.messages.append({"role": "assistant", "content": accumulated_text or "", "tool_calls": tool_calls_msg})

            for tc_id, tc_data in pending_tool_calls.items():
                args = json.loads(tc_data["args"]) if tc_data["args"] else {}
                yield ToolCallComplete(id=tc_id, name=tc_data["name"], arguments=args)

                # Execute tool
                try:
                    result = self.tool_registry.dispatch(tc_data["name"], args)
                except Exception as e:
                    result = json.dumps({"error": str(e)})
                if len(result) > 2000:
                    result = result[:2000] + "\n... [truncated]"

                # Yield tool result for TUI display
                yield ToolResult(tool_name=tc_data["name"], result=result[:200])

                self.messages.append({"role": "tool", "tool_call_id": tc_id, "content": result})

            # Loop back for next LLM call
            continue
        else:
            # Final text response — store and finish
            self.messages.append({"role": "assistant", "content": accumulated_text})
            yield StreamDone()
            return

    # Max iterations: force synthesis
    yield from self._force_final_synthesis_stream()

def _force_final_synthesis_stream(self) -> Generator[StreamEvent, None, None]:
    """Force the LLM to respond without tools (streaming)."""
    self.messages.append({
        "role": "user",
        "content": "You have enough information. Do not call any more tools. "
                   "Provide the best final answer now, clearly noting uncertainty where needed.",
    })
    for event in self.provider.chat_stream(self._build_messages(), tools=None):
        if isinstance(event, TextDelta):
            yield event
        elif isinstance(event, StreamDone):
            yield event
            return
    yield StreamDone()
```

`ToolResult` is defined in Section 2 alongside the other event types. In the agent loop, it is yielded after dispatching each tool:

```python
# (ToolResult is already defined in base.py — see Section 2)
class ToolResult(StreamEvent):
    """Result from an executed tool call."""
    tool_name: str
    result: str  # Preview (first 200 chars)
```

### Backward compatibility

`chat()` (non-streaming) is refactored to consume `chat_stream()`:

```python
def chat(self, user_message: str) -> str:
    full_text = ""
    for event in self.chat_stream(user_message):
        if isinstance(event, TextDelta):
            full_text += event.text
    return full_text
```

## 5. TUI Streaming Renderer

### New file: `genomix/tui_renderer.py`

```python
class StreamingRenderer:
    """Renders streaming events to the terminal paragraph-by-paragraph."""

    def __init__(self, console: Console):
        self.console = console
        self._buffer = ""          # Current paragraph being streamed
        self._finalized = []       # Completed paragraphs (already rendered as Markdown)

    def handle_event(self, event: StreamEvent):
        if isinstance(event, TextDelta):
            self._buffer += event.text
            # Print raw character
            self.console.print(event.text, end="", highlight=False)

            # Check for paragraph boundary (double newline)
            if "\n\n" in self._buffer:
                parts = self._buffer.split("\n\n", 1)
                completed = parts[0]
                self._buffer = parts[1] if len(parts) > 1 else ""

                # Erase raw text of completed paragraph, re-render as Markdown
                self._rerender_paragraph(completed)

        elif isinstance(event, ToolCallStart):
            self._flush_buffer()
            self.console.print(f"  [dim #00d787]⚡ {event.name}[/]", end="")

        elif isinstance(event, ToolCallComplete):
            args_str = ", ".join(f"{k}={v!r}" for k, v in list(event.arguments.items())[:3])
            if len(args_str) > 50:
                args_str = args_str[:47] + "..."
            self.console.print(f"([dim]{args_str}[/])")

        elif isinstance(event, ToolResult):
            preview = event.result.replace("\n", " ")[:80]
            self.console.print(f"  [dim]  ↳ {preview}[/]")

        elif isinstance(event, StreamDone):
            self._flush_buffer()
            self.console.print()  # Final newline

    def _flush_buffer(self):
        """Render remaining buffer as Markdown."""
        if self._buffer.strip():
            # Move cursor up to erase raw text, re-render as Markdown
            self._rerender_paragraph(self._buffer)
            self._buffer = ""

    def _rerender_paragraph(self, text):
        """Replace raw text with Markdown-rendered version.

        Approach: Use Rich Live with a growing list of Renderables.
        - Completed paragraphs are rendered as Rich Markdown objects
        - The current streaming paragraph is rendered as plain Text
        - Rich Live updates the display in-place without flickering
        """
        self._finalized.append(Markdown(text))
        # Live context re-renders all finalized paragraphs + current buffer
```

### TUI integration

In `GenomixTUI._run_agent()`, replace:

```python
# OLD: spinner + full response
with self.console.status("🧬 Analyzing..."):
    response = loop.chat(message)
self.console.print(Markdown(response))

# NEW: streaming renderer with Rich Live
renderer = StreamingRenderer(self.console)
self.console.print()
for event in loop.chat_stream(message):
    renderer.handle_event(event)
```

**Rendering approach: Rich Live**

The `StreamingRenderer` uses `rich.live.Live` internally:
- It maintains a `Group` of renderables: finalized paragraphs (Markdown) + current buffer (Text)
- On each `TextDelta`: append to buffer, update the Live display
- On paragraph boundary (`\n\n`): convert buffer to `Markdown`, add to finalized list, clear buffer
- On `StreamDone`: finalize remaining buffer, stop Live
- Tool calls (`ToolCallStart`, `ToolResult`) are printed OUTSIDE Live (using `live.console.print()`) to avoid them being overwritten

This avoids ANSI cursor manipulation entirely — Rich handles all terminal positioning.

### Deprecation of callbacks

The existing `AgentLoop` callback parameters (`on_tool_call`, `on_tool_result`, `on_thinking`) are deprecated. They remain in the constructor signature for backward compatibility but are not called in the streaming path. The `chat()` non-streaming wrapper does not fire them either — callers should migrate to `chat_stream()` events. The callbacks will be removed in v0.3.0.

### Swarm manager

Swarm-launched analyses continue to use `chat()` (non-streaming). Streaming is interactive-only. This is explicitly out of scope for this spec.

## 6. Edge Cases

| Case | Behavior |
|------|----------|
| Provider doesn't support streaming | Fallback: `chat()` + fake stream (yield full text as one TextDelta) |
| Network error mid-stream | Catch exception, yield what we have, print error |
| Tool call fails | Yield ToolResult with error message, continue loop |
| Empty response | Yield TextDelta("No response generated.") |
| Max iterations reached | Call `_force_final_synthesis_stream()` which streams the forced response |
| Context compression needed | Compress before each provider call (same as current) |
| Non-interactive mode (`genomix ask`) | Uses `chat()` which accumulates from `chat_stream()` internally |

## 7. Files Changed

| File | Action | What changes |
|------|--------|-------------|
| `genomix/providers/base.py` | Modify | Add StreamEvent dataclasses, `chat_stream()` abstract method |
| `genomix/providers/opencode.py` | Modify | Implement `chat_stream()` with httpx SSE |
| `genomix/providers/claude.py` | Modify | Implement `chat_stream()` with Anthropic SDK |
| `genomix/providers/openai_provider.py` | Modify | Implement `chat_stream()` with OpenAI SDK |
| `genomix/agent/loop.py` | Modify | Add `chat_stream()` generator, refactor `chat()` to use it |
| `genomix/tui.py` | Modify | Replace spinner with StreamingRenderer |
| `genomix/tui_renderer.py` | Create | StreamingRenderer class |
| `tests/unit/test_streaming.py` | Create | Tests for events, mock streaming, renderer |

## 8. Testing Strategy

- **Unit tests for StreamEvent types**: construction, equality
- **Mock streaming provider**: yields canned events, verify agent loop handles them correctly
- **Tool call accumulation**: verify partial ToolCallArgs are assembled into complete ToolCallComplete
- **Renderer paragraph detection**: verify double-newline triggers re-render
- **Backward compatibility**: verify `chat()` still works and returns same results
- **Integration**: mock provider that yields text + tool calls + text, verify full flow
