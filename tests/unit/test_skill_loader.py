from pathlib import Path
from genomix.skills.loader import load_skill


def test_load_skill(fixtures_dir):
    skill = load_skill(fixtures_dir / "sample_skill" / "SKILL.md")
    assert skill.metadata.name == "test-skill"
    assert skill.metadata.description == "A test skill for unit tests"
    assert skill.metadata.version == "1.0.0"
    assert "test" in skill.metadata.tags
    assert "Do step one" in skill.body


def test_load_skill_missing_file():
    result = load_skill(Path("/nonexistent/SKILL.md"))
    assert result is None
