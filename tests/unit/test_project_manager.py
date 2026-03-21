from pathlib import Path
import pytest
import yaml

from genomix.project.manager import ProjectManager, GenomixProject, ProjectNotFoundError


def test_init_creates_project(tmp_path):
    pm = ProjectManager(tmp_path)
    project = pm.init(name="Test Project", organism="Homo sapiens", reference_genome="GRCh38", data_type="whole_genome_sequencing")
    assert (tmp_path / ".genomix" / "project.yaml").exists()
    assert (tmp_path / ".gitignore").exists()
    assert project.name == "Test Project"
    assert project.organism == "Homo sapiens"


def test_init_creates_directory_structure(tmp_path):
    pm = ProjectManager(tmp_path)
    pm.init(name="T", organism="E. coli", reference_genome="K12", data_type="wgs")
    assert (tmp_path / "data" / "raw").is_dir()
    assert (tmp_path / "data" / "processed").is_dir()
    assert (tmp_path / "reports").is_dir()
    assert (tmp_path / ".genomix" / "runtime" / "swarm").is_dir()
    assert (tmp_path / ".genomix" / "cache").is_dir()
    assert (tmp_path / ".genomix" / "skills").is_dir()


def test_discover_finds_project(tmp_path):
    pm = ProjectManager(tmp_path)
    pm.init(name="T", organism="o", reference_genome="r", data_type="d")
    subdir = tmp_path / "data" / "raw"
    found = ProjectManager.discover(subdir)
    assert found.root == tmp_path


def test_discover_raises_when_not_found(tmp_path):
    with pytest.raises(ProjectNotFoundError):
        ProjectManager.discover(tmp_path)


def test_load_project(tmp_path):
    pm = ProjectManager(tmp_path)
    pm.init(name="My Project", organism="Mus musculus", reference_genome="mm39", data_type="wes")
    project = pm.load()
    assert project.name == "My Project"
    assert project.organism == "Mus musculus"
    assert project.reference_genome == "mm39"


def test_init_adds_gitignore_entry(tmp_path):
    pm = ProjectManager(tmp_path)
    pm.init(name="T", organism="o", reference_genome="r", data_type="d")
    gitignore = (tmp_path / ".gitignore").read_text()
    assert ".genomix/" in gitignore
