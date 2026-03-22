"""Streaming renderer — displays LLM responses progressively with Rich."""
from __future__ import annotations

from rich.console import Console
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
            if self._finalized_text.strip():
                self.console.print()
                self.console.print(Markdown(self._finalized_text.strip()))
            self.console.print()

    def _update_live(self) -> None:
        display_text = self._finalized_text + self._buffer
        if not display_text.strip():
            return
        if self._live is None:
            self._live = Live(Text(display_text), console=self.console, refresh_per_second=10)
            self._live.start()
        else:
            self._live.update(Text(display_text))

    def _stop_live(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
