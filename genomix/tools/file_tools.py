"""Built-in file tools for the agent."""
import gzip
import json
import os
from pathlib import Path

MAX_PREVIEW_LINES = 200
MAX_PREVIEW_CHARS = 50_000


def _open_text_file(path: Path):
    if path.suffix in {".gz", ".bgz"}:
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("rt", encoding="utf-8", errors="replace")


def _read_preview(path: Path) -> str:
    lines: list[str] = []
    chars = 0
    truncated_by_chars = False
    truncated_by_lines = False

    with _open_text_file(path) as handle:
        for raw_line in handle:
            if len(lines) >= MAX_PREVIEW_LINES:
                truncated_by_lines = True
                break

            remaining = MAX_PREVIEW_CHARS - chars
            if remaining <= 0:
                truncated_by_chars = True
                break

            if len(raw_line) > remaining:
                lines.append(raw_line[:remaining])
                chars += remaining
                truncated_by_chars = True
                break

            lines.append(raw_line)
            chars += len(raw_line)

    preview = "".join(lines)
    if not (truncated_by_lines or truncated_by_chars):
        return preview

    header = f"(showing first {len(lines)} lines"
    if truncated_by_chars:
        header += f", truncated at {MAX_PREVIEW_CHARS} chars"
    header += ")\n"
    return header + preview


def read_file(args):
    try:
        return _read_preview(Path(args["path"]).expanduser())
    except Exception as e:
        return json.dumps({"error": str(e)})


def list_dir(args):
    try:
        return json.dumps(sorted(os.listdir(args.get("path", "."))))
    except Exception as e:
        return json.dumps({"error": str(e)})


def register_file_tools(registry):
    registry.register(
        name="read_file",
        description="Read a file's contents",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        handler=read_file,
    )
    registry.register(
        name="list_dir",
        description="List directory contents",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        handler=list_dir,
    )
