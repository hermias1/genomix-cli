from pathlib import Path
import pytest
from genomix.skills.registry import SkillRegistry


def test_discover_skills(fixtures_dir, tmp_path):
    skills_dir = tmp_path / "skills" / "test-category" / "test-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text((fixtures_dir / "sample_skill" / "SKILL.md").read_text())
    registry = SkillRegistry([tmp_path / "skills"])
    skills = registry.list_skills()
    assert len(skills) >= 1
    assert any(s.name == "test-skill" for s in skills)


def test_get_skill_by_path(fixtures_dir, tmp_path):
    skills_dir = tmp_path / "skills" / "test-category" / "test-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text((fixtures_dir / "sample_skill" / "SKILL.md").read_text())
    registry = SkillRegistry([tmp_path / "skills"])
    skill = registry.get_skill_by_path("test-category/test-skill")
    assert skill is not None
    assert skill.metadata.name == "test-skill"
