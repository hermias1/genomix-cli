"""Genomix project management: init, discover, load."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


class ProjectNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class GenomixProject:
    root: Path
    name: str
    organism: str
    reference_genome: str
    data_type: str
    created_at: str
    tools: dict[str, str]

    @classmethod
    def from_yaml(cls, root: Path, data: dict[str, Any]) -> GenomixProject:
        return cls(
            root=root, name=data["name"], organism=data["organism"],
            reference_genome=data["reference_genome"], data_type=data["data_type"],
            created_at=data.get("created_at", ""), tools=data.get("tools", {}),
        )


class ProjectManager:
    def __init__(self, root: Path):
        self.root = root

    def init(self, name: str, organism: str, reference_genome: str, data_type: str) -> GenomixProject:
        genomix_dir = self.root / ".genomix"
        genomix_dir.mkdir(parents=True, exist_ok=True)
        for d in ["data/raw", "data/processed", "reports", ".genomix/runtime/swarm", ".genomix/cache", ".genomix/cache/references", ".genomix/cache/databases", ".genomix/skills"]:
            (self.root / d).mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc).isoformat()
        manifest = {"schema_version": 1, "name": name, "organism": organism, "reference_genome": reference_genome, "data_type": data_type, "created_at": now, "tools": {"aligner": "bwa-mem2", "variant_caller": "gatk", "annotator": "snpeff"}}
        with open(genomix_dir / "project.yaml", "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
        gitignore_path = self.root / ".gitignore"
        lines = gitignore_path.read_text().splitlines() if gitignore_path.exists() else []
        if ".genomix/" not in lines:
            lines.append(".genomix/")
            gitignore_path.write_text("\n".join(lines) + "\n")
        return GenomixProject.from_yaml(self.root, manifest)

    def load(self) -> GenomixProject:
        manifest_path = self.root / ".genomix" / "project.yaml"
        if not manifest_path.exists():
            raise ProjectNotFoundError(f"No project found at {self.root}")
        with open(manifest_path) as f:
            data = yaml.safe_load(f)
        return GenomixProject.from_yaml(self.root, data)

    @classmethod
    def discover(cls, start: Path) -> GenomixProject:
        current = start.resolve()
        while True:
            if (current / ".genomix" / "project.yaml").exists():
                return cls(current).load()
            parent = current.parent
            if parent == current:
                raise ProjectNotFoundError(f"No genomix project found from {start} upward.")
            current = parent
