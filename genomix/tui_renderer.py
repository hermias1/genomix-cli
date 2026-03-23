"""Streaming renderer — displays LLM responses progressively with Rich."""
from __future__ import annotations

import sys

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from genomix.providers.base import (
    StreamEvent, TextDelta, ToolCallStart, ToolCallComplete,
    ToolResult, ErrorEvent, StreamDone,
)


class StreamingRenderer:
    """Renders streaming events to terminal.

    Strategy: print text character-by-character during streaming (raw),
    then on StreamDone, clear and re-render as Markdown.
    Tool calls are printed immediately.
    """

    def __init__(self, console: Console):
        self.console = console
        self._buffer = ""
        self._thinking_live: Live | None = None
        self._got_first_text = False
        self._raw_lines_count = 0

    def show_thinking(self) -> None:
        """Show a thinking indicator before the first event arrives."""
        from rich.spinner import Spinner
        self._thinking_live = Live(
            Spinner("dots", text="[dim #00d787] 🧬 Thinking...[/]", style="#00d787"),
            console=self.console,
            refresh_per_second=10,
        )
        self._thinking_live.start()

    def _dismiss_thinking(self) -> None:
        if self._thinking_live is not None:
            self._thinking_live.stop()
            self._thinking_live = None

    def handle_event(self, event: StreamEvent) -> None:
        if isinstance(event, TextDelta):
            if not self._got_first_text:
                self._got_first_text = True
                self._dismiss_thinking()
            # Print raw characters as they stream
            sys.stdout.write(event.text)
            sys.stdout.flush()
            self._buffer += event.text
            self._raw_lines_count += event.text.count("\n")

        elif isinstance(event, ToolCallStart):
            self._dismiss_thinking()
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
            self._dismiss_thinking()
            self.console.print(f"\n[red]Error: {event.message}[/]")

        elif isinstance(event, StreamDone):
            self._dismiss_thinking()
            if self._buffer.strip():
                # Move cursor up to erase raw streamed text
                if self._raw_lines_count > 0:
                    sys.stdout.write(f"\033[{self._raw_lines_count + 1}A\033[J")
                    sys.stdout.flush()
                else:
                    # Single line — just clear it
                    sys.stdout.write("\r\033[K")
                    sys.stdout.flush()
                # Re-render as formatted Markdown
                self.console.print()
                self.console.print(Markdown(self._buffer.strip()))
            self.console.print()
