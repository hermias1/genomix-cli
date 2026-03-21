from genomix.agent.prompt_builder import build_system_prompt
from genomix.project.manager import GenomixProject
from pathlib import Path


def test_build_system_prompt_minimal():
    prompt = build_system_prompt(project=None, skill_body=None, privacy_mode=False)
    assert "Genomix" in prompt
    assert "genome" in prompt.lower() or "bioinformatics" in prompt.lower()


def test_build_system_prompt_with_project():
    project = GenomixProject(root=Path("/tmp/test"), name="BRCA Study", organism="Homo sapiens", reference_genome="GRCh38", data_type="wgs", created_at="2026-03-21", tools={"aligner": "bwa-mem2"})
    prompt = build_system_prompt(project=project, skill_body=None, privacy_mode=False)
    assert "BRCA Study" in prompt
    assert "Homo sapiens" in prompt
    assert "GRCh38" in prompt


def test_build_system_prompt_with_skill():
    prompt = build_system_prompt(project=None, skill_body="When the user asks about variants, do X then Y.", privacy_mode=False)
    assert "variants" in prompt


def test_build_system_prompt_privacy_mode():
    prompt = build_system_prompt(project=None, skill_body=None, privacy_mode=True)
    assert "privacy" in prompt.lower() or "never" in prompt.lower()
