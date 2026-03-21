"""Registry for discovering and looking up skills."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from genomix.skills.loader import Skill, SkillMetadata, load_skill


class SkillRegistry:
    """Discovers SKILL.md files under one or more skill directories."""

    def __init__(self, skill_dirs: list[Path]) -> None:
        self._dirs = skill_dirs
        self._cache: Optional[dict[str, Skill]] = None  # keyed by relative path

    def _build_cache(self) -> dict[str, Skill]:
        cache: dict[str, Skill] = {}
        for base in self._dirs:
            for skill_file in base.rglob("SKILL.md"):
                skill = load_skill(skill_file)
                if skill is None:
                    continue
                # relative path from base, without the trailing SKILL.md
                rel = skill_file.parent.relative_to(base)
                cache[str(rel)] = skill
        return cache

    def _get_cache(self) -> dict[str, Skill]:
        if self._cache is None:
            self._cache = self._build_cache()
        return self._cache

    def list_skills(self) -> list[SkillMetadata]:
        """Return metadata for all discovered skills."""
        return [skill.metadata for skill in self._get_cache().values()]

    def get_skill_by_path(self, path: str) -> Optional[Skill]:
        """Look up a skill by its relative directory path (e.g. 'category/skill-name')."""
        return self._get_cache().get(path)

    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """Look up the first skill whose metadata name matches."""
        for skill in self._get_cache().values():
            if skill.metadata.name == name:
                return skill
        return None
