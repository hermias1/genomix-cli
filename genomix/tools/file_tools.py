"""Built-in file tools for the agent."""
import json
import os
from pathlib import Path


def read_file(args):
    try:
        content = Path(args["path"]).read_text()
        lines = content.splitlines()
        if len(lines) > 200:
            return f"(showing first 200 of {len(lines)} lines)\n" + "\n".join(lines[:200])
        return content
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
