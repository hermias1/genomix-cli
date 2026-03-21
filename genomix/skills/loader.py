"""Parse SKILL.md files into structured Skill objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class SkillMetadata:
    name: str
    description: str = ""
    version: str = ""
    author: str = ""
    license: str = ""
    tags: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)


@dataclass
class Skill:
    metadata: SkillMetadata
    body: str
    path: Optional[Path] = None


def load_skill(path: Path) -> Optional[Skill]:
    """Parse a SKILL.md file. Returns None if the file does not exist."""
    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8")

    # Split YAML frontmatter from body
    frontmatter: dict = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()

    genomix_meta = (frontmatter.get("metadata") or {}).get("genomix") or {}

    metadata = SkillMetadata(
        name=frontmatter.get("name", ""),
        description=frontmatter.get("description", ""),
        version=str(frontmatter.get("version", "")),
        author=frontmatter.get("author", ""),
        license=frontmatter.get("license", ""),
        tags=genomix_meta.get("tags", []),
        tools_used=genomix_meta.get("tools_used", []),
    )

    return Skill(metadata=metadata, body=body, path=path)
