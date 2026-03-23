"""Context compression: summarize old tool results when context grows."""
from __future__ import annotations
from typing import Any

CHARS_PER_TOKEN = 4


def estimate_tokens(messages):
    total_chars = sum(len(m.get("content", "") or "") for m in messages)
    return total_chars // CHARS_PER_TOKEN


def should_compress(messages, max_tokens):
    return estimate_tokens(messages) > max_tokens * 0.8


def compress_messages(messages, max_tokens):
    if not should_compress(messages, max_tokens):
        return messages
    result = []
    if messages and messages[0]["role"] == "system":
        result.append(messages[0])
        messages = messages[1:]
    keep_recent = min(6, len(messages))
    old = messages[:-keep_recent] if keep_recent < len(messages) else []
    recent = messages[-keep_recent:]
    for msg in old:
        if msg.get("role") == "tool" and len(msg.get("content", "") or "") > 500:
            msg = {**msg, "content": (msg["content"] or "")[:200] + "\n... [truncated]"}
        result.append(msg)
    result.extend(recent)
    return result
