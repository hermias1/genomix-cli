"""Base provider interface for AI backends."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Generator


class StreamEvent:
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


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ProviderResponse:
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


class BaseProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> ProviderResponse: ...
    @abstractmethod
    def chat_stream(self, messages, tools=None) -> Generator[StreamEvent, None, None]:
        """Streaming: yields StreamEvents."""
        ...
    @abstractmethod
    def supports_tool_calling(self) -> bool: ...
    @abstractmethod
    def max_context_length(self) -> int: ...
