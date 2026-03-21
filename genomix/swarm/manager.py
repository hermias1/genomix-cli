"""Swarm manager: track background analyses."""
import json, uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SwarmTask:
    id: str
    command: str
    args: list[str]
    status: TaskStatus = TaskStatus.PENDING
    pid: int | None = None
    progress: str = ""
    output: str = ""
    error: str = ""


class SwarmManager:
    def __init__(self, state_dir, max_concurrent=4):
        self.state_dir = Path(state_dir)
        self.max_concurrent = max_concurrent
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def submit(self, command, args):
        task = SwarmTask(id=uuid.uuid4().hex[:8], command=command, args=args)
        self._save(task)
        return task

    def list_tasks(self):
        return [self._load(f) for f in sorted(self.state_dir.glob("*.json"))]

    def get_task(self, task_id):
        path = self.state_dir / f"{task_id}.json"
        return self._load(path) if path.exists() else None

    def cancel(self, task_id):
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.CANCELLED
            self._save(task)

    def update(self, task_id, **kwargs):
        task = self.get_task(task_id)
        if task:
            for k, v in kwargs.items():
                if hasattr(task, k): setattr(task, k, v)
            self._save(task)

    def _save(self, task):
        path = self.state_dir / f"{task.id}.json"
        path.write_text(json.dumps({"id": task.id, "command": task.command, "args": task.args,
            "status": task.status.value, "pid": task.pid, "progress": task.progress,
            "output": task.output, "error": task.error}, indent=2))

    def _load(self, path):
        data = json.loads(Path(path).read_text())
        return SwarmTask(id=data["id"], command=data["command"], args=data["args"],
            status=TaskStatus(data["status"]), pid=data.get("pid"),
            progress=data.get("progress", ""), output=data.get("output", ""), error=data.get("error", ""))
