# Genomix CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an AI-powered CLI tool that orchestrates bioinformatics tools and databases for DNA/genome analysis via natural language and slash commands.

**Architecture:** Python CLI (prompt_toolkit) wrapping an LLM agent loop that calls bioinformatics tools via MCP servers. Project-scoped (`.genomix/`), skill-driven, with background analysis support (swarm). Provider-agnostic (Claude/OpenAI/Ollama).

**Tech Stack:** Python 3.11+, prompt_toolkit, anthropic SDK, openai SDK, mcp SDK, pyyaml, httpx, rich

**Spec:** `docs/superpowers/specs/2026-03-21-genomix-cli-design.md`

---

## File Structure

```
genomix-cli/
├── pyproject.toml                         # Package metadata, entry points, dependencies
├── requirements.txt                       # Pinned dependencies
├── LICENSE                                # Apache 2.0
├── .gitignore
│
├── genomix/
│   ├── __init__.py                        # Version string
│   ├── cli.py                             # Entry point: argparse (setup/init/run/ask) + interactive TUI
│   ├── config.py                          # Load/merge ~/.genomix/ + .genomix/ configs + secrets
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── loop.py                        # Conversation loop: send to LLM, handle tool calls, iterate
│   │   ├── prompt_builder.py              # Assemble system prompt from project + skills context
│   │   └── context_compressor.py          # Summarize old tool results when context grows large
│   │
│   ├── providers/
│   │   ├── __init__.py                    # get_provider(name) factory
│   │   ├── base.py                        # BaseProvider ABC
│   │   ├── claude.py                      # Anthropic API implementation
│   │   ├── openai_provider.py             # OpenAI API implementation
│   │   └── opencode.py                    # Ollama local implementation
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py                    # ToolRegistry: register, list schemas, dispatch calls
│   │   ├── file_tools.py                  # read_file, write_file, list_dir, search_files
│   │   └── mcp_bridge.py                  # MCPBridge: discover, connect, proxy MCP server tools
│   │
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── loader.py                      # Parse SKILL.md (YAML frontmatter + markdown body)
│   │   └── registry.py                    # SkillRegistry: list, search, load by name/command
│   │
│   ├── project/
│   │   ├── __init__.py
│   │   ├── manager.py                     # ProjectManager: init, discover, load, validate
│   │   └── setup_wizard.py               # Detect OS, check binaries, install via brew/apt/conda
│   │
│   └── swarm/
│       ├── __init__.py
│       └── manager.py                     # SwarmManager: spawn, track, notify background analyses
│
├── mcp_servers/
│   ├── __init__.py
│   ├── base_biotool.py                    # Shared base for all biotool MCP servers
│   ├── base_database.py                   # Shared base for all database MCP servers
│   ├── biotools/
│   │   ├── __init__.py
│   │   ├── samtools_server.py             # samtools MCP server (view, sort, index, stats, depth, flagstat)
│   │   ├── bwa_server.py                  # bwa/bwa-mem2 MCP server (mem, index)
│   │   ├── gatk_server.py                 # GATK MCP server (HaplotypeCaller, BaseRecalibrator, MarkDuplicates)
│   │   ├── blast_server.py                # BLAST+ MCP server (blastn, blastp, blastx, makeblastdb)
│   │   └── fastqc_server.py              # FastQC MCP server (analyze, report)
│   └── databases/
│       ├── __init__.py
│       ├── ncbi_server.py                 # NCBI MCP server (Entrez search, fetch, BLAST API)
│       ├── ensembl_server.py              # Ensembl REST API MCP server
│       ├── clinvar_server.py              # ClinVar MCP server (variant significance)
│       └── dbsnp_server.py               # dbSNP MCP server (variant catalog)
│
├── skills/                                # 12 built-in SKILL.md files
│   ├── sequencing/
│   │   ├── quality-control/SKILL.md
│   │   ├── alignment/SKILL.md
│   │   ├── variant-calling/SKILL.md
│   │   └── annotation/SKILL.md
│   ├── comparative/
│   │   ├── blast-analysis/SKILL.md
│   │   ├── multiple-alignment/SKILL.md
│   │   └── phylogenetics/SKILL.md
│   ├── exploration/
│   │   ├── sequence-summary/SKILL.md
│   │   ├── database-search/SKILL.md
│   │   └── variant-explain/SKILL.md
│   └── common/
│       ├── file-formats/SKILL.md
│       └── genome-references/SKILL.md
│
├── tests/
│   ├── conftest.py                        # Shared fixtures, tmp project dirs
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_project_manager.py
│   │   ├── test_skill_loader.py
│   │   ├── test_skill_registry.py
│   │   ├── test_tool_registry.py
│   │   ├── test_provider_base.py
│   │   ├── test_prompt_builder.py
│   │   ├── test_agent_loop.py
│   │   ├── test_swarm_manager.py
│   │   ├── test_mcp_bridge.py
│   │   └── test_cli.py
│   ├── integration/
│   │   ├── test_samtools_server.py
│   │   └── test_ncbi_server.py
│   └── fixtures/
│       ├── tiny.fasta                     # 2 sequences, ~200bp each
│       ├── tiny.fastq                     # 10 reads, 150bp
│       ├── tiny.vcf                       # 5 variants
│       └── sample_skill/
│           └── SKILL.md                   # Test skill fixture
```

---

## Task 1: Package Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `genomix/__init__.py`
- Create: `genomix/cli.py`

- [ ] **Step 1: Write test for CLI entry point**

Create `tests/unit/test_cli.py`:
```python
import subprocess
import sys


def test_genomix_help():
    """genomix --help should exit 0 and show usage."""
    result = subprocess.run(
        [sys.executable, "-m", "genomix.cli", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "genomix" in result.stdout.lower()


def test_genomix_version():
    """genomix --version should print the version string."""
    result = subprocess.run(
        [sys.executable, "-m", "genomix.cli", "--version"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_cli.py -v`
Expected: FAIL — module `genomix.cli` not found

- [ ] **Step 3: Create package files**

Create `pyproject.toml`:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "genomix-cli"
version = "0.1.0"
description = "AI-powered CLI for DNA sequence and genome analysis"
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.11"
authors = [{ name = "Genomix Contributors" }]
keywords = ["genomics", "bioinformatics", "dna", "cli", "ai"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: Apache Software License",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
]
dependencies = [
    "prompt-toolkit>=3.0",
    "anthropic>=0.40",
    "openai>=1.50",
    "pyyaml>=6.0",
    "httpx>=0.27",
    "rich>=13.0",
    "mcp>=1.0",
]

[project.scripts]
genomix = "genomix.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Create `requirements.txt`:
```
prompt-toolkit>=3.0
anthropic>=0.40
openai>=1.50
pyyaml>=6.0
httpx>=0.27
rich>=13.0
mcp>=1.0
pytest>=8.0
```

Create `LICENSE` with Apache 2.0 text.

Create `.gitignore`:
```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.genomix/
.env
*.bam
*.bai
*.vcf.gz
*.fastq.gz
.pytest_cache/
```

Create `genomix/__init__.py`:
```python
"""Genomix CLI — AI-powered DNA sequence and genome analysis."""

__version__ = "0.1.0"
```

Create `genomix/cli.py`:
```python
"""Genomix CLI entry point."""

import argparse
import sys

from genomix import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genomix",
        description="AI-powered CLI for DNA sequence and genome analysis",
    )
    parser.add_argument(
        "--version", action="version", version=f"genomix {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("setup", help="Install dependencies and configure AI provider")
    subparsers.add_parser("init", help="Initialize a new genomix project")

    run_parser = subparsers.add_parser("run", help="Run a slash command non-interactively")
    run_parser.add_argument("slash_command", help="Slash command (e.g. /qc)")
    run_parser.add_argument("args", nargs="*", help="Command arguments")
    run_parser.add_argument("--output", "-o", help="Output path override")
    run_parser.add_argument("--format", choices=["text", "json"], default="text")

    ask_parser = subparsers.add_parser("ask", help="Ask a question non-interactively")
    ask_parser.add_argument("question", nargs="*", help="Question text")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        # Interactive mode — will be implemented in Task 12
        print(f"🧬 Genomix CLI v{__version__}")
        print("Interactive mode not yet implemented. Use --help for available commands.")
        return 0

    print(f"Command '{args.command}' not yet implemented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Create `tests/__init__.py` and `tests/unit/__init__.py` (empty).

Create `tests/conftest.py`:
```python
"""Shared test fixtures."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory."""
    return tmp_path


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures."""
    return Path(__file__).parent / "fixtures"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pip install -e ".[dev]" && pytest tests/unit/test_cli.py -v`
Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml requirements.txt LICENSE .gitignore genomix/ tests/
git commit -m "feat: scaffold genomix-cli package with CLI entry point"
```

---

## Task 2: Config System

**Files:**
- Create: `genomix/config.py`
- Create: `tests/unit/test_config.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_config.py`:
```python
import os
from pathlib import Path

import pytest
import yaml

from genomix.config import GenomixConfig, load_config, load_secrets


def test_default_config():
    """Default config has sane defaults."""
    config = GenomixConfig()
    assert config.provider == "claude"
    assert config.model == "claude-sonnet-4-6"
    assert config.max_concurrent_swarm == 4


def test_load_config_from_yaml(tmp_path):
    """Config loads from a YAML file and merges with defaults."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "provider": {"default": "openai", "model": "gpt-4o"},
    }))
    config = load_config(config_path=config_file)
    assert config.provider == "openai"
    assert config.model == "gpt-4o"
    assert config.max_concurrent_swarm == 4  # default preserved


def test_load_config_missing_file():
    """Missing config file returns defaults."""
    config = load_config(config_path=Path("/nonexistent/config.yaml"))
    assert config.provider == "claude"


def test_load_secrets(tmp_path):
    """Secrets are loaded from secrets.yaml."""
    secrets_file = tmp_path / "secrets.yaml"
    secrets_file.write_text(yaml.dump({
        "anthropic_api_key": "sk-ant-test",
        "ncbi_api_key": "ncbi123",
    }))
    secrets = load_secrets(secrets_path=secrets_file)
    assert secrets["anthropic_api_key"] == "sk-ant-test"
    assert secrets["ncbi_api_key"] == "ncbi123"


def test_load_secrets_missing_file():
    """Missing secrets file returns empty dict."""
    secrets = load_secrets(secrets_path=Path("/nonexistent/secrets.yaml"))
    assert secrets == {}


def test_config_mcp_servers(tmp_path):
    """MCP server config is parsed correctly."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "mcp_servers": {
            "samtools": {"enabled": True, "binary_path": "/usr/bin/samtools"},
            "cosmic": {"enabled": False},
        },
    }))
    config = load_config(config_path=config_file)
    assert config.mcp_servers["samtools"]["enabled"] is True
    assert config.mcp_servers["samtools"]["binary_path"] == "/usr/bin/samtools"
    assert config.mcp_servers["cosmic"]["enabled"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_config.py -v`
Expected: FAIL — `genomix.config` not found

- [ ] **Step 3: Implement config.py**

Create `genomix/config.py`:
```python
"""Configuration loading for Genomix CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

GENOMIX_HOME = Path(os.environ.get("GENOMIX_HOME", Path.home() / ".genomix"))


@dataclass
class GenomixConfig:
    """Merged configuration from defaults + file."""

    provider: str = "claude"
    model: str = "claude-sonnet-4-6"
    max_concurrent_swarm: int = 4
    mcp_servers: dict[str, dict[str, Any]] = field(default_factory=dict)
    privacy_mode: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GenomixConfig:
        provider_data = data.get("provider", {})
        return cls(
            provider=provider_data.get("default", "claude"),
            model=provider_data.get("model", "claude-sonnet-4-6"),
            max_concurrent_swarm=data.get("max_concurrent_swarm", 4),
            mcp_servers=data.get("mcp_servers", {}),
            privacy_mode=data.get("privacy_mode", False),
        )


def load_config(config_path: Path | None = None) -> GenomixConfig:
    """Load config from YAML file, falling back to defaults."""
    if config_path is None:
        config_path = GENOMIX_HOME / "config.yaml"
    if not config_path.exists():
        return GenomixConfig()
    with open(config_path) as f:
        data = yaml.safe_load(f) or {}
    return GenomixConfig.from_dict(data)


def load_secrets(secrets_path: Path | None = None) -> dict[str, str]:
    """Load secrets from secrets.yaml."""
    if secrets_path is None:
        secrets_path = GENOMIX_HOME / "secrets.yaml"
    if not secrets_path.exists():
        return {}
    with open(secrets_path) as f:
        data = yaml.safe_load(f) or {}
    return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_config.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/config.py tests/unit/test_config.py
git commit -m "feat: add config and secrets loading system"
```

---

## Task 3: Project Manager

**Files:**
- Create: `genomix/project/__init__.py`
- Create: `genomix/project/manager.py`
- Create: `tests/unit/test_project_manager.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_project_manager.py`:
```python
from pathlib import Path

import pytest
import yaml

from genomix.project.manager import (
    ProjectManager,
    GenomixProject,
    ProjectNotFoundError,
)


def test_init_creates_project(tmp_path):
    """init() creates .genomix/ with project.yaml."""
    pm = ProjectManager(tmp_path)
    project = pm.init(
        name="Test Project",
        organism="Homo sapiens",
        reference_genome="GRCh38",
        data_type="whole_genome_sequencing",
    )
    assert (tmp_path / ".genomix" / "project.yaml").exists()
    assert (tmp_path / ".gitignore").exists()
    assert project.name == "Test Project"
    assert project.organism == "Homo sapiens"


def test_init_creates_directory_structure(tmp_path):
    """init() creates data/ and reports/ directories."""
    pm = ProjectManager(tmp_path)
    pm.init(name="T", organism="E. coli", reference_genome="K12", data_type="wgs")
    assert (tmp_path / "data" / "raw").is_dir()
    assert (tmp_path / "data" / "processed").is_dir()
    assert (tmp_path / "reports").is_dir()
    assert (tmp_path / ".genomix" / "runtime" / "swarm").is_dir()
    assert (tmp_path / ".genomix" / "cache").is_dir()
    assert (tmp_path / ".genomix" / "skills").is_dir()


def test_discover_finds_project(tmp_path):
    """discover() walks up to find .genomix/project.yaml."""
    pm = ProjectManager(tmp_path)
    pm.init(name="T", organism="o", reference_genome="r", data_type="d")
    subdir = tmp_path / "data" / "raw"
    found = ProjectManager.discover(subdir)
    assert found.root == tmp_path


def test_discover_raises_when_not_found(tmp_path):
    """discover() raises ProjectNotFoundError when no project exists."""
    with pytest.raises(ProjectNotFoundError):
        ProjectManager.discover(tmp_path)


def test_load_project(tmp_path):
    """load() reads an existing project.yaml."""
    pm = ProjectManager(tmp_path)
    pm.init(name="My Project", organism="Mus musculus", reference_genome="mm39", data_type="wes")
    project = pm.load()
    assert project.name == "My Project"
    assert project.organism == "Mus musculus"
    assert project.reference_genome == "mm39"


def test_init_adds_gitignore_entry(tmp_path):
    """init() adds .genomix/ to .gitignore."""
    pm = ProjectManager(tmp_path)
    pm.init(name="T", organism="o", reference_genome="r", data_type="d")
    gitignore = (tmp_path / ".gitignore").read_text()
    assert ".genomix/" in gitignore
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_project_manager.py -v`
Expected: FAIL

- [ ] **Step 3: Implement project manager**

Create `genomix/project/__init__.py` (empty).

Create `genomix/project/manager.py`:
```python
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
    """Immutable validated project metadata."""

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
            root=root,
            name=data["name"],
            organism=data["organism"],
            reference_genome=data["reference_genome"],
            data_type=data["data_type"],
            created_at=data.get("created_at", ""),
            tools=data.get("tools", {}),
        )


class ProjectManager:
    """Manage genomix projects."""

    def __init__(self, root: Path):
        self.root = root

    def init(
        self,
        name: str,
        organism: str,
        reference_genome: str,
        data_type: str,
    ) -> GenomixProject:
        """Initialize a new genomix project."""
        genomix_dir = self.root / ".genomix"
        genomix_dir.mkdir(parents=True, exist_ok=True)

        # Create directory structure
        for d in [
            "data/raw", "data/processed", "reports",
            ".genomix/runtime/swarm", ".genomix/cache",
            ".genomix/cache/references", ".genomix/cache/databases",
            ".genomix/skills",
        ]:
            (self.root / d).mkdir(parents=True, exist_ok=True)

        # Write project.yaml
        now = datetime.now(timezone.utc).isoformat()
        manifest = {
            "schema_version": 1,
            "name": name,
            "organism": organism,
            "reference_genome": reference_genome,
            "data_type": data_type,
            "created_at": now,
            "tools": {
                "aligner": "bwa-mem2",
                "variant_caller": "gatk",
                "annotator": "snpeff",
            },
        }
        manifest_path = genomix_dir / "project.yaml"
        with open(manifest_path, "w") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

        # Add .genomix/ to .gitignore
        gitignore_path = self.root / ".gitignore"
        lines = []
        if gitignore_path.exists():
            lines = gitignore_path.read_text().splitlines()
        if ".genomix/" not in lines:
            lines.append(".genomix/")
            gitignore_path.write_text("\n".join(lines) + "\n")

        return GenomixProject.from_yaml(self.root, manifest)

    def load(self) -> GenomixProject:
        """Load project from .genomix/project.yaml."""
        manifest_path = self.root / ".genomix" / "project.yaml"
        if not manifest_path.exists():
            raise ProjectNotFoundError(f"No project found at {self.root}")
        with open(manifest_path) as f:
            data = yaml.safe_load(f)
        return GenomixProject.from_yaml(self.root, data)

    @classmethod
    def discover(cls, start: Path) -> GenomixProject:
        """Walk up from start to find a genomix project."""
        current = start.resolve()
        while True:
            manifest = current / ".genomix" / "project.yaml"
            if manifest.exists():
                pm = cls(current)
                return pm.load()
            parent = current.parent
            if parent == current:
                raise ProjectNotFoundError(
                    f"No genomix project found from {start} upward. Run 'genomix init'."
                )
            current = parent
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_project_manager.py -v`
Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/project/ tests/unit/test_project_manager.py
git commit -m "feat: add project manager with init, discover, load"
```

---

## Task 4: Provider Abstraction + Claude Provider

**Files:**
- Create: `genomix/providers/__init__.py`
- Create: `genomix/providers/base.py`
- Create: `genomix/providers/claude.py`
- Create: `tests/unit/test_provider_base.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_provider_base.py`:
```python
import pytest

from genomix.providers.base import BaseProvider, ToolCall, ProviderResponse
from genomix.providers import get_provider


def test_base_provider_is_abstract():
    """BaseProvider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseProvider()


def test_provider_response_has_content_or_tool_calls():
    """ProviderResponse stores text content and/or tool calls."""
    resp = ProviderResponse(content="Hello", tool_calls=[])
    assert resp.content == "Hello"
    assert resp.tool_calls == []


def test_tool_call_structure():
    """ToolCall has id, name, and arguments."""
    tc = ToolCall(id="call_1", name="samtools_stats", arguments={"bam_path": "x.bam"})
    assert tc.name == "samtools_stats"
    assert tc.arguments["bam_path"] == "x.bam"


def test_get_provider_claude():
    """get_provider('claude') returns a ClaudeProvider."""
    from genomix.providers.claude import ClaudeProvider
    provider = get_provider("claude", api_key="test-key", model="claude-sonnet-4-6")
    assert isinstance(provider, ClaudeProvider)


def test_get_provider_unknown():
    """get_provider with unknown name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("unknown_provider")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_provider_base.py -v`
Expected: FAIL

- [ ] **Step 3: Implement providers**

Create `genomix/providers/base.py`:
```python
"""Base provider interface for AI backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """A tool call requested by the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ProviderResponse:
    """Response from an AI provider."""
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


class BaseProvider(ABC):
    """Abstract base for AI providers."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> ProviderResponse:
        """Send messages, receive response with optional tool calls."""

    @abstractmethod
    def supports_tool_calling(self) -> bool:
        """Whether this provider supports native tool calling."""

    @abstractmethod
    def max_context_length(self) -> int:
        """Maximum context window size in tokens."""
```

Create `genomix/providers/claude.py`:
```python
"""Claude (Anthropic) provider implementation."""

from __future__ import annotations

import json
from typing import Any

import anthropic

from genomix.providers.base import BaseProvider, ProviderResponse, ToolCall

MODEL_CONTEXT = {
    "claude-sonnet-4-6": 200_000,
    "claude-opus-4-6": 200_000,
    "claude-haiku-4-5-20251001": 200_000,
}


class ClaudeProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> ProviderResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 8192,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = [self._convert_tool(t) for t in tools]

        response = self.client.messages.create(**kwargs)

        content = None
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content = block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input,
                ))
        return ProviderResponse(content=content, tool_calls=tool_calls)

    def supports_tool_calling(self) -> bool:
        return True

    def max_context_length(self) -> int:
        return MODEL_CONTEXT.get(self.model, 200_000)

    @staticmethod
    def _convert_tool(tool: dict[str, Any]) -> dict[str, Any]:
        """Convert OpenAI-style tool schema to Anthropic format."""
        if "function" in tool:
            func = tool["function"]
            return {
                "name": func["name"],
                "description": func.get("description", ""),
                "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
            }
        return tool
```

Create `genomix/providers/__init__.py`:
```python
"""AI provider factory."""

from __future__ import annotations

from typing import Any

from genomix.providers.base import BaseProvider


def get_provider(name: str, **kwargs: Any) -> BaseProvider:
    """Get a provider instance by name."""
    if name == "claude":
        from genomix.providers.claude import ClaudeProvider
        return ClaudeProvider(
            api_key=kwargs.get("api_key", ""),
            model=kwargs.get("model", "claude-sonnet-4-6"),
        )
    elif name == "openai":
        from genomix.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(
            api_key=kwargs.get("api_key", ""),
            model=kwargs.get("model", "gpt-4o"),
        )
    elif name == "opencode":
        from genomix.providers.opencode import OpenCodeProvider
        return OpenCodeProvider(
            endpoint=kwargs.get("endpoint", "http://localhost:11434"),
            model=kwargs.get("model", "llama3.3:70b"),
        )
    else:
        raise ValueError(f"Unknown provider: {name}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_provider_base.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/providers/ tests/unit/test_provider_base.py
git commit -m "feat: add provider abstraction with Claude implementation"
```

---

## Task 5: Tool Registry

**Files:**
- Create: `genomix/tools/__init__.py`
- Create: `genomix/tools/registry.py`
- Create: `tests/unit/test_tool_registry.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_tool_registry.py`:
```python
import pytest

from genomix.tools.registry import ToolRegistry


@pytest.fixture
def registry():
    return ToolRegistry()


def test_register_and_list(registry):
    """Registered tools appear in list."""
    registry.register(
        name="samtools_stats",
        description="Get alignment statistics",
        parameters={"type": "object", "properties": {"bam_path": {"type": "string"}}, "required": ["bam_path"]},
        handler=lambda args: '{"reads": 1000}',
    )
    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0]["function"]["name"] == "samtools_stats"


def test_dispatch_calls_handler(registry):
    """dispatch() calls the correct handler."""
    registry.register(
        name="echo",
        description="Echo back",
        parameters={"type": "object", "properties": {"text": {"type": "string"}}},
        handler=lambda args: f"echo: {args['text']}",
    )
    result = registry.dispatch("echo", {"text": "hello"})
    assert result == "echo: hello"


def test_dispatch_unknown_tool(registry):
    """dispatch() raises KeyError for unknown tool."""
    with pytest.raises(KeyError, match="Unknown tool"):
        registry.dispatch("nonexistent", {})


def test_list_tools_returns_openai_format(registry):
    """list_tools() returns OpenAI function-calling format."""
    registry.register(
        name="my_tool",
        description="A tool",
        parameters={"type": "object", "properties": {}},
        handler=lambda args: "",
    )
    schema = registry.list_tools()[0]
    assert schema["type"] == "function"
    assert "function" in schema
    assert schema["function"]["name"] == "my_tool"
    assert schema["function"]["description"] == "A tool"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_tool_registry.py -v`
Expected: FAIL

- [ ] **Step 3: Implement tool registry**

Create `genomix/tools/__init__.py` (empty).

Create `genomix/tools/registry.py`:
```python
"""Centralized tool registry for Genomix."""

from __future__ import annotations

from typing import Any, Callable


class ToolRegistry:
    """Register, list, and dispatch tool calls."""

    def __init__(self):
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[[dict[str, Any]], str],
    ) -> None:
        """Register a tool with its schema and handler."""
        self._tools[name] = {
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
            "handler": handler,
        }

    def list_tools(self) -> list[dict[str, Any]]:
        """Return tool schemas in OpenAI function-calling format."""
        return [t["schema"] for t in self._tools.values()]

    def dispatch(self, name: str, arguments: dict[str, Any]) -> str:
        """Call a tool by name and return its result as a string."""
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name]["handler"](arguments)

    def has_tool(self, name: str) -> bool:
        return name in self._tools
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_tool_registry.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/tools/ tests/unit/test_tool_registry.py
git commit -m "feat: add centralized tool registry"
```

---

## Task 6: Skills System

**Files:**
- Create: `genomix/skills/__init__.py`
- Create: `genomix/skills/loader.py`
- Create: `genomix/skills/registry.py`
- Create: `tests/unit/test_skill_loader.py`
- Create: `tests/unit/test_skill_registry.py`
- Create: `tests/fixtures/sample_skill/SKILL.md`

- [ ] **Step 1: Write failing tests**

Create `tests/fixtures/sample_skill/SKILL.md`:
```markdown
---
name: test-skill
description: A test skill for unit tests
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [test]
    tools_used: [samtools_stats]
---

# Test Skill

When the user asks for a test:
1. Do step one
2. Do step two
```

Create `tests/unit/test_skill_loader.py`:
```python
from pathlib import Path

from genomix.skills.loader import load_skill, SkillMetadata


def test_load_skill(fixtures_dir):
    """load_skill parses frontmatter and body."""
    skill = load_skill(fixtures_dir / "sample_skill" / "SKILL.md")
    assert skill.metadata.name == "test-skill"
    assert skill.metadata.description == "A test skill for unit tests"
    assert skill.metadata.version == "1.0.0"
    assert "test" in skill.metadata.tags
    assert "Do step one" in skill.body


def test_load_skill_missing_file():
    """load_skill returns None for missing file."""
    result = load_skill(Path("/nonexistent/SKILL.md"))
    assert result is None
```

Create `tests/unit/test_skill_registry.py`:
```python
from pathlib import Path

import pytest

from genomix.skills.registry import SkillRegistry


def test_discover_skills(fixtures_dir, tmp_path):
    """Registry discovers skills from a directory."""
    # Create a skills dir with one skill
    skills_dir = tmp_path / "skills" / "test-category" / "test-skill"
    skills_dir.mkdir(parents=True)
    (fixtures_dir / "sample_skill" / "SKILL.md").read_text()
    (skills_dir / "SKILL.md").write_text(
        (fixtures_dir / "sample_skill" / "SKILL.md").read_text()
    )
    registry = SkillRegistry([tmp_path / "skills"])
    skills = registry.list_skills()
    assert len(skills) >= 1
    assert any(s.name == "test-skill" for s in skills)


def test_get_skill_by_path(fixtures_dir, tmp_path):
    """get_skill_by_path loads a specific skill."""
    skills_dir = tmp_path / "skills" / "test-category" / "test-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text(
        (fixtures_dir / "sample_skill" / "SKILL.md").read_text()
    )
    registry = SkillRegistry([tmp_path / "skills"])
    skill = registry.get_skill_by_path("test-category/test-skill")
    assert skill is not None
    assert skill.metadata.name == "test-skill"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_skill_loader.py tests/unit/test_skill_registry.py -v`
Expected: FAIL

- [ ] **Step 3: Implement skills system**

Create `genomix/skills/__init__.py` (empty).

Create `genomix/skills/loader.py`:
```python
"""Parse SKILL.md files (YAML frontmatter + markdown body)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SkillMetadata:
    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    license: str = ""
    tags: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SkillMetadata:
        metadata = data.get("metadata", {}).get("genomix", {})
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            license=data.get("license", ""),
            tags=metadata.get("tags", []),
            tools_used=metadata.get("tools_used", []),
        )


@dataclass
class Skill:
    metadata: SkillMetadata
    body: str
    path: Path


def load_skill(path: Path) -> Skill | None:
    """Load a SKILL.md file, parsing YAML frontmatter and markdown body."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return Skill(
            metadata=SkillMetadata(name=path.parent.name, description=""),
            body=text,
            path=path,
        )
    parts = text.split("---", 2)
    if len(parts) < 3:
        return Skill(
            metadata=SkillMetadata(name=path.parent.name, description=""),
            body=text,
            path=path,
        )
    frontmatter = yaml.safe_load(parts[1]) or {}
    body = parts[2].strip()
    return Skill(
        metadata=SkillMetadata.from_dict(frontmatter),
        body=body,
        path=path,
    )
```

Create `genomix/skills/registry.py`:
```python
"""Skill registry: discover, list, and load skills."""

from __future__ import annotations

from pathlib import Path

from genomix.skills.loader import Skill, SkillMetadata, load_skill


class SkillRegistry:
    """Manage skill discovery and loading."""

    def __init__(self, skill_dirs: list[Path]):
        self._skill_dirs = skill_dirs
        self._cache: dict[str, Skill] = {}
        self._discover()

    def _discover(self) -> None:
        """Scan skill directories for SKILL.md files."""
        for base_dir in self._skill_dirs:
            if not base_dir.exists():
                continue
            for skill_file in base_dir.rglob("SKILL.md"):
                rel = skill_file.parent.relative_to(base_dir)
                path_key = str(rel)
                skill = load_skill(skill_file)
                if skill:
                    self._cache[path_key] = skill

    def list_skills(self) -> list[SkillMetadata]:
        """Return metadata for all discovered skills."""
        return [s.metadata for s in self._cache.values()]

    def get_skill_by_path(self, path: str) -> Skill | None:
        """Load a skill by its relative path (e.g. 'sequencing/quality-control')."""
        return self._cache.get(path)

    def get_skill_by_name(self, name: str) -> Skill | None:
        """Load a skill by its name field."""
        for skill in self._cache.values():
            if skill.metadata.name == name:
                return skill
        return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_skill_loader.py tests/unit/test_skill_registry.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/skills/ tests/unit/test_skill_loader.py tests/unit/test_skill_registry.py tests/fixtures/
git commit -m "feat: add skills system with SKILL.md parsing and registry"
```

---

## Task 7: Prompt Builder

**Files:**
- Create: `genomix/agent/__init__.py`
- Create: `genomix/agent/prompt_builder.py`
- Create: `tests/unit/test_prompt_builder.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_prompt_builder.py`:
```python
from genomix.agent.prompt_builder import build_system_prompt
from genomix.project.manager import GenomixProject


def test_build_system_prompt_minimal():
    """System prompt includes genomix identity."""
    prompt = build_system_prompt(project=None, skill_body=None, privacy_mode=False)
    assert "Genomix" in prompt
    assert "bioinformatics" in prompt.lower() or "genome" in prompt.lower()


def test_build_system_prompt_with_project():
    """System prompt includes project context."""
    project = GenomixProject(
        root="/tmp/test",
        name="BRCA Study",
        organism="Homo sapiens",
        reference_genome="GRCh38",
        data_type="wgs",
        created_at="2026-03-21",
        tools={"aligner": "bwa-mem2"},
    )
    prompt = build_system_prompt(project=project, skill_body=None, privacy_mode=False)
    assert "BRCA Study" in prompt
    assert "Homo sapiens" in prompt
    assert "GRCh38" in prompt


def test_build_system_prompt_with_skill():
    """System prompt includes loaded skill instructions."""
    prompt = build_system_prompt(
        project=None,
        skill_body="When the user asks about variants, do X then Y.",
        privacy_mode=False,
    )
    assert "variants" in prompt


def test_build_system_prompt_privacy_mode():
    """Privacy mode adds data handling instructions."""
    prompt = build_system_prompt(project=None, skill_body=None, privacy_mode=True)
    assert "privacy" in prompt.lower() or "never send raw" in prompt.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_prompt_builder.py -v`
Expected: FAIL

- [ ] **Step 3: Implement prompt builder**

Create `genomix/agent/__init__.py` (empty).

Create `genomix/agent/prompt_builder.py`:
```python
"""Assemble the system prompt from project context, skills, and mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from genomix.project.manager import GenomixProject

IDENTITY = """You are Genomix, an AI assistant specialized in DNA sequence and genome analysis.
You help biologists, bioinformaticians, and researchers analyze genomic data by orchestrating
bioinformatics tools and querying genomic databases.

You are proactive: suggest next steps, explain results in accessible language, and adapt
your communication to the user's expertise level. When a user speaks in natural language,
explain in plain terms. When they use slash commands, be concise and technical.

You have access to tools for: file manipulation, sequence alignment, variant calling,
annotation, BLAST searches, database queries (NCBI, Ensembl, ClinVar, dbSNP), and more.
Always explain which tool you're using and why."""

PRIVACY_ADDENDUM = """
PRIVACY MODE IS ACTIVE. You must follow these rules strictly:
- Never include raw sequence data (nucleotide strings) in your responses or reasoning
- Never include patient identifiers or sample metadata
- Only reference aggregated statistics, variant IDs (rsIDs), and gene symbols
- All tools run locally — only summaries are passed to you"""


def build_system_prompt(
    project: GenomixProject | None,
    skill_body: str | None,
    privacy_mode: bool,
) -> str:
    """Build the full system prompt."""
    parts = [IDENTITY]

    if project:
        parts.append(f"""
## Active Project
- **Name:** {project.name}
- **Organism:** {project.organism}
- **Reference genome:** {project.reference_genome}
- **Data type:** {project.data_type}
- **Project root:** {project.root}""")

    if skill_body:
        parts.append(f"\n## Current Task Instructions\n\n{skill_body}")

    if privacy_mode:
        parts.append(PRIVACY_ADDENDUM)

    return "\n".join(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_prompt_builder.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/agent/ tests/unit/test_prompt_builder.py
git commit -m "feat: add prompt builder with project and privacy context"
```

---

## Task 8: Agent Loop

**Files:**
- Create: `genomix/agent/loop.py`
- Create: `tests/unit/test_agent_loop.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_agent_loop.py`:
```python
import pytest

from genomix.agent.loop import AgentLoop
from genomix.providers.base import BaseProvider, ProviderResponse, ToolCall
from genomix.tools.registry import ToolRegistry


class MockProvider(BaseProvider):
    """Provider that returns canned responses."""

    def __init__(self, responses: list[ProviderResponse]):
        self._responses = list(responses)
        self._call_count = 0

    def chat(self, messages, tools=None):
        resp = self._responses[self._call_count]
        self._call_count += 1
        return resp

    def supports_tool_calling(self):
        return True

    def max_context_length(self):
        return 200_000


def test_simple_conversation():
    """Agent returns text response for simple question."""
    provider = MockProvider([ProviderResponse(content="The genome has 3 billion base pairs.")])
    registry = ToolRegistry()
    loop = AgentLoop(provider=provider, tool_registry=registry)
    response = loop.chat("How large is the human genome?")
    assert "3 billion" in response


def test_tool_call_loop():
    """Agent calls a tool, feeds result back, and gets final answer."""
    provider = MockProvider([
        ProviderResponse(
            content=None,
            tool_calls=[ToolCall(id="c1", name="count_reads", arguments={"path": "x.bam"})],
        ),
        ProviderResponse(content="The file has 1000 reads."),
    ])
    registry = ToolRegistry()
    registry.register(
        name="count_reads",
        description="Count reads",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}},
        handler=lambda args: '{"count": 1000}',
    )
    loop = AgentLoop(provider=provider, tool_registry=registry)
    response = loop.chat("How many reads in x.bam?")
    assert "1000" in response


def test_max_iterations_guard():
    """Agent stops after max_iterations to prevent infinite loops."""
    # Provider always returns tool calls
    infinite_tool_call = ProviderResponse(
        content=None,
        tool_calls=[ToolCall(id="c1", name="noop", arguments={})],
    )
    provider = MockProvider([infinite_tool_call] * 50)
    registry = ToolRegistry()
    registry.register(
        name="noop", description="", parameters={"type": "object", "properties": {}},
        handler=lambda args: "ok",
    )
    loop = AgentLoop(provider=provider, tool_registry=registry, max_iterations=3)
    response = loop.chat("Do something")
    assert response  # Should return something, not hang
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_agent_loop.py -v`
Expected: FAIL

- [ ] **Step 3: Implement agent loop**

Create `genomix/agent/loop.py`:
```python
"""Conversational agent loop with tool calling."""

from __future__ import annotations

from typing import Any

from genomix.providers.base import BaseProvider, ProviderResponse
from genomix.tools.registry import ToolRegistry


class AgentLoop:
    """Run a conversation loop: LLM ↔ tool calls ↔ user."""

    def __init__(
        self,
        provider: BaseProvider,
        tool_registry: ToolRegistry,
        system_prompt: str = "",
        max_iterations: int = 30,
    ):
        self.provider = provider
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.messages: list[dict[str, Any]] = []

    def chat(self, user_message: str) -> str:
        """Process a user message and return the assistant's final text response."""
        self.messages.append({"role": "user", "content": user_message})

        all_messages = self._build_messages()
        tools = self.tool_registry.list_tools() or None

        for _ in range(self.max_iterations):
            response = self.provider.chat(all_messages, tools=tools)

            if response.tool_calls:
                # Add assistant message with tool calls
                all_messages.append({
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": [
                        {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                        for tc in response.tool_calls
                    ],
                })
                # Execute each tool call and add results
                for tc in response.tool_calls:
                    try:
                        result = self.tool_registry.dispatch(tc.name, tc.arguments)
                    except Exception as e:
                        result = f"Error: {e}"
                    all_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
            else:
                # Final text response
                text = response.content or ""
                self.messages.append({"role": "assistant", "content": text})
                return text

        # Max iterations reached
        return "I've reached the maximum number of steps. Please try a more specific request."

    def _build_messages(self) -> list[dict[str, Any]]:
        """Build the full message list with system prompt."""
        msgs: list[dict[str, Any]] = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.extend(self.messages)
        return msgs
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_agent_loop.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/agent/loop.py tests/unit/test_agent_loop.py
git commit -m "feat: add agent conversation loop with tool calling"
```

---

## Task 9: MCP Bridge

**Files:**
- Create: `genomix/tools/mcp_bridge.py`
- Create: `tests/unit/test_mcp_bridge.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_mcp_bridge.py`:
```python
import pytest

from genomix.tools.mcp_bridge import MCPBridge, MCPServerConfig


def test_server_config():
    """MCPServerConfig stores server connection details."""
    config = MCPServerConfig(
        name="samtools",
        command="python",
        args=["-m", "mcp_servers.biotools.samtools_server"],
        enabled=True,
    )
    assert config.name == "samtools"
    assert config.enabled is True


def test_bridge_register_server():
    """Bridge accepts server configs."""
    bridge = MCPBridge()
    config = MCPServerConfig(
        name="samtools",
        command="python",
        args=["-m", "mcp_servers.biotools.samtools_server"],
        enabled=True,
    )
    bridge.register_server(config)
    assert "samtools" in bridge.registered_servers


def test_bridge_disabled_server_not_registered():
    """Disabled servers are tracked but not connected."""
    bridge = MCPBridge()
    config = MCPServerConfig(
        name="cosmic",
        command="python",
        args=["-m", "mcp_servers.databases.cosmic_server"],
        enabled=False,
    )
    bridge.register_server(config)
    assert "cosmic" in bridge.registered_servers
    assert not bridge.registered_servers["cosmic"].enabled
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mcp_bridge.py -v`
Expected: FAIL

- [ ] **Step 3: Implement MCP bridge**

Create `genomix/tools/mcp_bridge.py`:
```python
"""MCP Bridge: discover, connect, and proxy MCP server tools."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from genomix.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    timeout: int = 120


class MCPBridge:
    """Manage MCP server connections and proxy tool calls."""

    def __init__(self):
        self.registered_servers: dict[str, MCPServerConfig] = {}
        self._connections: dict[str, Any] = {}  # Will hold MCP client sessions
        self._loop: asyncio.AbstractEventLoop | None = None

    def register_server(self, config: MCPServerConfig) -> None:
        """Register an MCP server configuration."""
        self.registered_servers[config.name] = config

    async def connect_server(self, name: str) -> list[dict[str, Any]]:
        """Connect to an MCP server and return its tool schemas."""
        config = self.registered_servers.get(name)
        if not config or not config.enabled:
            return []

        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env or None,
            )
            read, write = await stdio_client(params).__aenter__()
            session = await ClientSession(read, write).__aenter__()
            await session.initialize()

            self._connections[name] = session

            result = await session.list_tools()
            tools = []
            for tool in result.tools:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": f"mcp_{name}_{tool.name}",
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                })
            return tools

        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{name}': {e}")
            return []

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call a tool on a connected MCP server."""
        session = self._connections.get(server_name)
        if not session:
            return json.dumps({"error": f"Server '{server_name}' not connected"})

        try:
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else "{}"
        except Exception as e:
            return json.dumps({"error": str(e)})

    def register_tools_to_registry(
        self, tool_registry: ToolRegistry, tools: list[dict[str, Any]], server_name: str
    ) -> None:
        """Register MCP tools into the main tool registry."""
        for tool_schema in tools:
            func = tool_schema["function"]
            full_name = func["name"]  # Already prefixed with mcp_{server}_
            # Extract the original tool name (remove mcp_{server}_ prefix)
            original_name = full_name.removeprefix(f"mcp_{server_name}_")

            tool_registry.register(
                name=full_name,
                description=func["description"],
                parameters=func["parameters"],
                handler=lambda args, sn=server_name, tn=original_name: asyncio.get_event_loop().run_until_complete(
                    self.call_tool(sn, tn, args)
                ),
            )

    async def shutdown(self) -> None:
        """Close all MCP server connections."""
        for name, session in self._connections.items():
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass
        self._connections.clear()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mcp_bridge.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/tools/mcp_bridge.py tests/unit/test_mcp_bridge.py
git commit -m "feat: add MCP bridge for server management and tool proxying"
```

---

## Task 10: Samtools MCP Server (Reference Implementation)

**Files:**
- Create: `mcp_servers/__init__.py`
- Create: `mcp_servers/base_biotool.py`
- Create: `mcp_servers/biotools/__init__.py`
- Create: `mcp_servers/biotools/samtools_server.py`
- Create: `tests/integration/test_samtools_server.py`

- [ ] **Step 1: Write failing tests**

Create `tests/integration/__init__.py` (empty).

Create `tests/integration/test_samtools_server.py`:
```python
"""Integration tests for samtools MCP server — mocks subprocess calls."""

import json
from unittest.mock import patch, MagicMock

import pytest

from mcp_servers.base_biotool import BaseBiotoolServer


def test_base_biotool_check_binary():
    """check_binary returns True when binary is found."""
    with patch("shutil.which", return_value="/usr/bin/samtools"):
        server = BaseBiotoolServer(binary_name="samtools")
        assert server.check_binary() is True


def test_base_biotool_check_binary_missing():
    """check_binary returns False when binary is not found."""
    with patch("shutil.which", return_value=None):
        server = BaseBiotoolServer(binary_name="samtools")
        assert server.check_binary() is False


def test_base_biotool_run_command():
    """run_command executes binary and returns stdout."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "1000 reads"
    mock_result.stderr = ""
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        server = BaseBiotoolServer(binary_name="samtools")
        result = server.run_command(["stats", "input.bam"])
        mock_run.assert_called_once()
        assert "1000 reads" in result


def test_base_biotool_run_command_failure():
    """run_command returns error info on non-zero exit."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "file not found"
    with patch("subprocess.run", return_value=mock_result):
        server = BaseBiotoolServer(binary_name="samtools")
        result = server.run_command(["stats", "missing.bam"])
        assert "error" in result.lower() or "file not found" in result.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/integration/test_samtools_server.py -v`
Expected: FAIL

- [ ] **Step 3: Implement base biotool and samtools server**

Create `mcp_servers/__init__.py` (empty).

Create `mcp_servers/base_biotool.py`:
```python
"""Base class for bioinformatics tool MCP servers."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any


class BaseBiotoolServer:
    """Shared logic for MCP servers wrapping local binaries."""

    def __init__(self, binary_name: str, binary_path: str | None = None):
        self.binary_name = binary_name
        self.binary_path = binary_path or binary_name

    def check_binary(self) -> bool:
        """Check if the binary is available on PATH."""
        return shutil.which(self.binary_path) is not None

    def run_command(self, args: list[str], timeout: int = 300) -> str:
        """Run the binary with given arguments."""
        cmd = [self.binary_path] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                return json.dumps({
                    "error": f"{self.binary_name} exited with code {result.returncode}",
                    "stderr": result.stderr.strip(),
                    "command": " ".join(cmd),
                })
            return result.stdout
        except subprocess.TimeoutExpired:
            return json.dumps({"error": f"{self.binary_name} timed out after {timeout}s"})
        except FileNotFoundError:
            return json.dumps({
                "error": f"{self.binary_name} not found. Run 'genomix setup' to install it.",
            })
```

Create `mcp_servers/biotools/__init__.py` (empty).

Create `mcp_servers/biotools/samtools_server.py`:
```python
"""Samtools MCP server — exposes view, sort, index, stats, depth, flagstat."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from mcp_servers.base_biotool import BaseBiotoolServer

mcp = FastMCP("samtools")
_server = BaseBiotoolServer(binary_name="samtools")


@mcp.tool()
def samtools_stats(bam_path: str) -> str:
    """Get alignment statistics for a BAM file."""
    return _server.run_command(["stats", bam_path])


@mcp.tool()
def samtools_flagstat(bam_path: str) -> str:
    """Get flag statistics for a BAM file."""
    return _server.run_command(["flagstat", bam_path])


@mcp.tool()
def samtools_view(bam_path: str, region: str = "", flags: str = "") -> str:
    """View/filter alignments in a BAM file."""
    args = ["view"]
    if flags:
        args.extend(["-f", flags])
    args.append(bam_path)
    if region:
        args.append(region)
    return _server.run_command(args)


@mcp.tool()
def samtools_sort(bam_path: str, output_path: str) -> str:
    """Sort a BAM file."""
    return _server.run_command(["sort", "-o", output_path, bam_path])


@mcp.tool()
def samtools_index(bam_path: str) -> str:
    """Create an index for a BAM file."""
    result = _server.run_command(["index", bam_path])
    if not result.strip() or not result.startswith("{"):
        return json.dumps({"status": "ok", "index": f"{bam_path}.bai"})
    return result


@mcp.tool()
def samtools_depth(bam_path: str, region: str = "") -> str:
    """Calculate per-position depth in a BAM file."""
    args = ["depth"]
    if region:
        args.extend(["-r", region])
    args.append(bam_path)
    return _server.run_command(args)


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/integration/test_samtools_server.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_servers/ tests/integration/
git commit -m "feat: add base biotool server and samtools MCP server"
```

---

## Task 11: Remaining Biotools MCP Servers (bwa, gatk, blast, fastqc)

**Files:**
- Create: `mcp_servers/biotools/bwa_server.py`
- Create: `mcp_servers/biotools/gatk_server.py`
- Create: `mcp_servers/biotools/blast_server.py`
- Create: `mcp_servers/biotools/fastqc_server.py`

Each server follows the same pattern as samtools: import `BaseBiotoolServer`, create a `FastMCP` instance, define `@mcp.tool()` functions that delegate to `_server.run_command()`.

- [ ] **Step 1: Implement bwa_server.py**

```python
"""BWA/BWA-MEM2 MCP server — alignment of reads to reference genome."""

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_biotool import BaseBiotoolServer

mcp = FastMCP("bwa")
_server = BaseBiotoolServer(binary_name="bwa-mem2")


@mcp.tool()
def bwa_index(reference_fasta: str) -> str:
    """Build BWA index for a reference genome."""
    return _server.run_command(["index", reference_fasta])


@mcp.tool()
def bwa_mem(
    reference_fasta: str,
    read1_fastq: str,
    read2_fastq: str = "",
    threads: int = 4,
    output_sam: str = "output.sam",
) -> str:
    """Align reads to reference genome using BWA-MEM2."""
    args = ["mem", "-t", str(threads), reference_fasta, read1_fastq]
    if read2_fastq:
        args.append(read2_fastq)
    # BWA writes to stdout, capture and redirect
    result = _server.run_command(args)
    if not result.startswith("{"):
        import json
        with open(output_sam, "w") as f:
            f.write(result)
        return json.dumps({"status": "ok", "output": output_sam})
    return result


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 2: Implement gatk_server.py**

```python
"""GATK MCP server — variant calling and BAM processing."""

import json
from mcp.server.fastmcp import FastMCP
from mcp_servers.base_biotool import BaseBiotoolServer

mcp = FastMCP("gatk")
_server = BaseBiotoolServer(binary_name="gatk")


@mcp.tool()
def gatk_haplotype_caller(
    bam_path: str,
    reference_fasta: str,
    output_vcf: str,
    intervals: str = "",
) -> str:
    """Call germline variants using HaplotypeCaller."""
    args = ["HaplotypeCaller", "-I", bam_path, "-R", reference_fasta, "-O", output_vcf]
    if intervals:
        args.extend(["-L", intervals])
    result = _server.run_command(args, timeout=3600)
    if not result.startswith("{"):
        return json.dumps({"status": "ok", "output": output_vcf})
    return result


@mcp.tool()
def gatk_mark_duplicates(bam_path: str, output_bam: str, metrics_file: str = "dup_metrics.txt") -> str:
    """Mark duplicate reads in a BAM file."""
    args = ["MarkDuplicates", "-I", bam_path, "-O", output_bam, "-M", metrics_file]
    result = _server.run_command(args)
    if not result.startswith("{"):
        return json.dumps({"status": "ok", "output": output_bam, "metrics": metrics_file})
    return result


@mcp.tool()
def gatk_base_recalibrator(
    bam_path: str,
    reference_fasta: str,
    known_sites_vcf: str,
    output_table: str = "recal_data.table",
) -> str:
    """Generate base quality recalibration table."""
    args = [
        "BaseRecalibrator", "-I", bam_path, "-R", reference_fasta,
        "--known-sites", known_sites_vcf, "-O", output_table,
    ]
    result = _server.run_command(args)
    if not result.startswith("{"):
        return json.dumps({"status": "ok", "output": output_table})
    return result


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 3: Implement blast_server.py**

```python
"""BLAST+ MCP server — sequence similarity search."""

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_biotool import BaseBiotoolServer

mcp = FastMCP("blast")
_blastn = BaseBiotoolServer(binary_name="blastn")
_blastp = BaseBiotoolServer(binary_name="blastp")
_makeblastdb = BaseBiotoolServer(binary_name="makeblastdb")


@mcp.tool()
def blastn(query_fasta: str, database: str, evalue: str = "1e-5", max_target_seqs: int = 10, outfmt: str = "6") -> str:
    """Search nucleotide sequences against a nucleotide database."""
    return _blastn.run_command([
        "-query", query_fasta, "-db", database,
        "-evalue", evalue, "-max_target_seqs", str(max_target_seqs),
        "-outfmt", outfmt,
    ])


@mcp.tool()
def blastp(query_fasta: str, database: str, evalue: str = "1e-5", max_target_seqs: int = 10, outfmt: str = "6") -> str:
    """Search protein sequences against a protein database."""
    return _blastp.run_command([
        "-query", query_fasta, "-db", database,
        "-evalue", evalue, "-max_target_seqs", str(max_target_seqs),
        "-outfmt", outfmt,
    ])


@mcp.tool()
def makeblastdb(input_fasta: str, dbtype: str = "nucl", title: str = "") -> str:
    """Create a BLAST database from a FASTA file."""
    args = ["-in", input_fasta, "-dbtype", dbtype]
    if title:
        args.extend(["-title", title])
    return _makeblastdb.run_command(args)


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Implement fastqc_server.py**

```python
"""FastQC MCP server — sequencing quality control."""

import json
from mcp.server.fastmcp import FastMCP
from mcp_servers.base_biotool import BaseBiotoolServer

mcp = FastMCP("fastqc")
_server = BaseBiotoolServer(binary_name="fastqc")


@mcp.tool()
def fastqc_analyze(input_files: str, output_dir: str = ".", threads: int = 2) -> str:
    """Run FastQC quality control on FASTQ/BAM files. input_files is space-separated."""
    args = ["-o", output_dir, "-t", str(threads)] + input_files.split()
    result = _server.run_command(args)
    if not result.startswith("{"):
        return json.dumps({"status": "ok", "output_dir": output_dir})
    return result


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 5: Commit**

```bash
git add mcp_servers/biotools/
git commit -m "feat: add bwa, gatk, blast, fastqc MCP servers"
```

---

## Task 12: Database MCP Servers (ncbi, ensembl, clinvar, dbsnp)

**Files:**
- Create: `mcp_servers/base_database.py`
- Create: `mcp_servers/databases/__init__.py`
- Create: `mcp_servers/databases/ncbi_server.py`
- Create: `mcp_servers/databases/ensembl_server.py`
- Create: `mcp_servers/databases/clinvar_server.py`
- Create: `mcp_servers/databases/dbsnp_server.py`
- Create: `tests/integration/test_ncbi_server.py`

- [ ] **Step 1: Write failing test for base database**

Create `tests/integration/test_ncbi_server.py`:
```python
"""Tests for database MCP servers — mocks HTTP calls."""

from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from mcp_servers.base_database import BaseDatabaseServer


def test_base_database_cache_key():
    """Cache key is deterministic for same inputs."""
    server = BaseDatabaseServer(name="test")
    key1 = server._cache_key("search", {"query": "BRCA1"})
    key2 = server._cache_key("search", {"query": "BRCA1"})
    key3 = server._cache_key("search", {"query": "TP53"})
    assert key1 == key2
    assert key1 != key3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_ncbi_server.py -v`
Expected: FAIL

- [ ] **Step 3: Implement database servers**

Create `mcp_servers/base_database.py`:
```python
"""Base class for database API MCP servers."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import httpx


class BaseDatabaseServer:
    """Shared logic for MCP servers wrapping remote APIs."""

    def __init__(self, name: str, base_url: str = "", api_key: str = ""):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self._cache: dict[str, str] = {}

    def _cache_key(self, endpoint: str, params: dict[str, Any]) -> str:
        raw = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, endpoint: str, params: dict[str, Any] | None = None, use_cache: bool = True) -> str:
        """HTTP GET with optional caching."""
        params = params or {}
        key = self._cache_key(endpoint, params)
        if use_cache and key in self._cache:
            return self._cache[key]

        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith("http") else endpoint
        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                result = response.text
                self._cache[key] = result
                return result
        except httpx.HTTPError as e:
            return json.dumps({"error": str(e)})
```

Create `mcp_servers/databases/__init__.py` (empty).

Create `mcp_servers/databases/ncbi_server.py`:
```python
"""NCBI MCP server — Entrez search, fetch, BLAST API."""

import json
from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("ncbi")
_server = BaseDatabaseServer(
    name="ncbi",
    base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
)


@mcp.tool()
def ncbi_search(database: str, query: str, max_results: int = 10) -> str:
    """Search NCBI databases (nuccore, protein, gene, snp, clinvar, etc.)."""
    return _server.get("esearch.fcgi", {
        "db": database, "term": query, "retmax": max_results, "retmode": "json",
    })


@mcp.tool()
def ncbi_fetch(database: str, ids: str, rettype: str = "fasta", retmode: str = "text") -> str:
    """Fetch records from NCBI by ID. ids is comma-separated."""
    return _server.get("efetch.fcgi", {
        "db": database, "id": ids, "rettype": rettype, "retmode": retmode,
    })


@mcp.tool()
def ncbi_summary(database: str, ids: str) -> str:
    """Get document summaries for NCBI IDs."""
    return _server.get("esummary.fcgi", {
        "db": database, "id": ids, "retmode": "json",
    })


@mcp.tool()
def ncbi_gene_info(gene_query: str) -> str:
    """Search for a gene and return its summary."""
    search_result = _server.get("esearch.fcgi", {
        "db": "gene", "term": gene_query, "retmax": 1, "retmode": "json",
    })
    try:
        data = json.loads(search_result)
        ids = data.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return json.dumps({"error": f"Gene '{gene_query}' not found"})
        return _server.get("esummary.fcgi", {
            "db": "gene", "id": ids[0], "retmode": "json",
        })
    except json.JSONDecodeError:
        return search_result


if __name__ == "__main__":
    mcp.run()
```

Create `mcp_servers/databases/ensembl_server.py`:
```python
"""Ensembl REST API MCP server."""

import json
from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("ensembl")
_server = BaseDatabaseServer(name="ensembl", base_url="https://rest.ensembl.org")


@mcp.tool()
def ensembl_lookup_gene(species: str, symbol: str) -> str:
    """Look up a gene by symbol."""
    return _server.get(f"lookup/symbol/{species}/{symbol}", {"content-type": "application/json"})


@mcp.tool()
def ensembl_get_sequence(id: str, type: str = "genomic") -> str:
    """Get sequence for an Ensembl ID."""
    return _server.get(f"sequence/id/{id}", {"type": type, "content-type": "application/json"})


@mcp.tool()
def ensembl_vep(species: str, hgvs_notation: str) -> str:
    """Predict variant effect using VEP."""
    return _server.get(f"vep/{species}/hgvs/{hgvs_notation}", {"content-type": "application/json"})


@mcp.tool()
def ensembl_variant_info(species: str, variant_id: str) -> str:
    """Get variant information by rsID."""
    return _server.get(f"variation/{species}/{variant_id}", {"content-type": "application/json"})


if __name__ == "__main__":
    mcp.run()
```

Create `mcp_servers/databases/clinvar_server.py`:
```python
"""ClinVar MCP server — clinical variant significance."""

import json
from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("clinvar")
_server = BaseDatabaseServer(name="clinvar", base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils")


@mcp.tool()
def clinvar_search(query: str, max_results: int = 10) -> str:
    """Search ClinVar for variants."""
    return _server.get("esearch.fcgi", {
        "db": "clinvar", "term": query, "retmax": max_results, "retmode": "json",
    })


@mcp.tool()
def clinvar_fetch(variant_ids: str) -> str:
    """Fetch ClinVar records by ID."""
    return _server.get("efetch.fcgi", {
        "db": "clinvar", "id": variant_ids, "rettype": "clinvarset", "retmode": "xml",
    })


@mcp.tool()
def clinvar_summary(variant_ids: str) -> str:
    """Get summary for ClinVar variant IDs."""
    return _server.get("esummary.fcgi", {
        "db": "clinvar", "id": variant_ids, "retmode": "json",
    })


if __name__ == "__main__":
    mcp.run()
```

Create `mcp_servers/databases/dbsnp_server.py`:
```python
"""dbSNP MCP server — known variant catalog."""

import json
from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("dbsnp")
_server = BaseDatabaseServer(name="dbsnp", base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils")


@mcp.tool()
def dbsnp_search(query: str, max_results: int = 10) -> str:
    """Search dbSNP for variants."""
    return _server.get("esearch.fcgi", {
        "db": "snp", "term": query, "retmax": max_results, "retmode": "json",
    })


@mcp.tool()
def dbsnp_fetch(rs_ids: str) -> str:
    """Fetch variant details by rsID (comma-separated numbers, without 'rs' prefix)."""
    return _server.get("efetch.fcgi", {
        "db": "snp", "id": rs_ids, "rettype": "json", "retmode": "text",
    })


@mcp.tool()
def dbsnp_summary(rs_ids: str) -> str:
    """Get summary for dbSNP IDs."""
    return _server.get("esummary.fcgi", {
        "db": "snp", "id": rs_ids, "retmode": "json",
    })


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/integration/test_ncbi_server.py -v`
Expected: 1 PASS

- [ ] **Step 5: Commit**

```bash
git add mcp_servers/base_database.py mcp_servers/databases/ tests/integration/test_ncbi_server.py
git commit -m "feat: add database MCP servers (ncbi, ensembl, clinvar, dbsnp)"
```

---

## Task 13: CLI/TUI with Interactive Mode

**Files:**
- Modify: `genomix/cli.py`
- Create: `tests/unit/test_cli.py` (extend)

- [ ] **Step 1: Write failing tests for interactive mode startup**

Add to `tests/unit/test_cli.py`:
```python
from unittest.mock import patch, MagicMock

from genomix.cli import build_parser, handle_setup, handle_init


def test_parser_subcommands():
    """Parser recognizes all subcommands."""
    parser = build_parser()
    for cmd in ["setup", "init", "run", "ask"]:
        args = parser.parse_args([cmd] if cmd not in ("run", "ask") else [cmd, "test"])
        assert args.command == cmd


def test_handle_init_calls_project_manager(tmp_path):
    """handle_init creates a project via ProjectManager."""
    with patch("genomix.cli.ProjectManager") as MockPM:
        mock_instance = MagicMock()
        MockPM.return_value = mock_instance
        mock_instance.init.return_value = MagicMock(name="Test")
        handle_init(tmp_path)
        mock_instance.init.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_cli.py -v`
Expected: New tests FAIL

- [ ] **Step 3: Extend cli.py with init handler and interactive shell stub**

Modify `genomix/cli.py` to add:
- `handle_init(path)` — wraps `ProjectManager.init()` with interactive prompts
- `handle_interactive()` — starts prompt_toolkit session (stub for now)
- Wire subcommands to handlers

The interactive mode will use `prompt_toolkit.PromptSession` with custom completer for slash commands.

```python
# Add to cli.py — key additions:

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from rich.console import Console

SLASH_COMMANDS = [
    "/qc", "/align", "/variant-call", "/annotate", "/pipeline",
    "/blast", "/msa", "/phylo",
    "/summary", "/search", "/explain",
    "/swarm", "/history", "/provider", "/model", "/help", "/quit",
]

COMMAND_SKILL_MAP = {
    "/qc": "sequencing/quality-control",
    "/align": "sequencing/alignment",
    "/variant-call": "sequencing/variant-calling",
    "/annotate": "sequencing/annotation",
    "/blast": "comparative/blast-analysis",
    "/msa": "comparative/multiple-alignment",
    "/phylo": "comparative/phylogenetics",
    "/summary": "exploration/sequence-summary",
    "/search": "exploration/database-search",
    "/explain": "exploration/variant-explain",
}


def handle_init(path):
    """Interactive project initialization."""
    from genomix.project.manager import ProjectManager
    console = Console()
    console.print("[bold]🧬 New Genomix Project[/bold]\n")
    name = input("Project name: ")
    organism = input("Organism: ")
    reference_genome = input("Reference genome: ")
    data_type = input("Data type: ")
    pm = ProjectManager(path)
    project = pm.init(name=name, organism=organism, reference_genome=reference_genome, data_type=data_type)
    console.print(f"\n[green]✓[/green] Project initialized: {project.name}")


def handle_interactive():
    """Start interactive TUI session."""
    console = Console()
    console.print(f"[bold]🧬 Genomix CLI v{__version__}[/bold]")
    console.print("Type your question or use /help\n")

    completer = WordCompleter(SLASH_COMMANDS, sentence=True)
    session = PromptSession(completer=completer)

    while True:
        try:
            user_input = session.prompt("genomix> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input in ("/quit", "/exit", "/q"):
            break
        if user_input == "/help":
            for cmd in SLASH_COMMANDS:
                console.print(f"  {cmd}")
            continue
        # TODO: wire to agent loop
        console.print(f"[dim](agent loop not yet wired — received: {user_input})[/dim]")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_cli.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/cli.py tests/unit/test_cli.py
git commit -m "feat: add interactive CLI with slash command completion"
```

---

## Task 14: Wire Everything Together

**Files:**
- Modify: `genomix/cli.py` — wire agent loop, provider, tools, skills, MCP bridge
- Create: `genomix/tools/file_tools.py`

This task connects all components: CLI → config → provider → agent loop → tool registry → MCP bridge → skills.

- [ ] **Step 1: Implement file_tools.py**

Create `genomix/tools/file_tools.py`:
```python
"""Built-in file tools for the agent."""

from __future__ import annotations

import json
import os
from pathlib import Path


def read_file(args: dict) -> str:
    path = args["path"]
    try:
        content = Path(path).read_text()
        lines = content.splitlines()
        if len(lines) > 200:
            return f"(showing first 200 of {len(lines)} lines)\n" + "\n".join(lines[:200])
        return content
    except Exception as e:
        return json.dumps({"error": str(e)})


def list_dir(args: dict) -> str:
    path = args.get("path", ".")
    try:
        entries = sorted(os.listdir(path))
        return json.dumps(entries)
    except Exception as e:
        return json.dumps({"error": str(e)})


def register_file_tools(registry):
    """Register file tools on the tool registry."""
    registry.register(
        name="read_file",
        description="Read a file's contents",
        parameters={"type": "object", "properties": {"path": {"type": "string", "description": "File path"}}, "required": ["path"]},
        handler=read_file,
    )
    registry.register(
        name="list_dir",
        description="List directory contents",
        parameters={"type": "object", "properties": {"path": {"type": "string", "description": "Directory path"}}, "required": ["path"]},
        handler=list_dir,
    )
```

- [ ] **Step 2: Wire the interactive loop in cli.py**

Add a `run_interactive()` function that:
1. Loads config + secrets
2. Creates provider via `get_provider()`
3. Creates `ToolRegistry`, registers file tools
4. Creates `SkillRegistry` pointing to `skills/` dir
5. Tries to discover project via `ProjectManager.discover()`
6. Builds system prompt via `build_system_prompt()`
7. Creates `AgentLoop`
8. In the prompt loop: handle slash commands (load skill → inject into system prompt), or pass to agent loop

- [ ] **Step 3: Run manual smoke test**

Run: `python -m genomix.cli`
Expected: Interactive prompt appears, `/help` works, typing a message prints agent response (or error if no API key)

- [ ] **Step 4: Commit**

```bash
git add genomix/cli.py genomix/tools/file_tools.py
git commit -m "feat: wire CLI to agent loop, providers, skills, and tools"
```

---

## Task 15: Setup Wizard

**Files:**
- Create: `genomix/project/setup_wizard.py`

- [ ] **Step 1: Write failing test**

Create test in `tests/unit/test_cli.py` (extend):
```python
from genomix.project.setup_wizard import check_binary, REQUIRED_BINARIES


def test_check_binary_returns_tuple():
    """check_binary returns (name, found, version_or_none)."""
    name, found, version = check_binary("python3")
    assert name == "python3"
    assert isinstance(found, bool)
```

- [ ] **Step 2: Implement setup_wizard.py**

```python
"""Setup wizard: detect OS, check binaries, install missing dependencies."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass

REQUIRED_BINARIES = [
    ("samtools", "samtools --version"),
    ("bwa-mem2", "bwa-mem2 version"),
    ("gatk", "gatk --version"),
    ("blastn", "blastn -version"),
    ("fastqc", "fastqc --version"),
]

BREW_PACKAGES = {
    "samtools": "samtools",
    "bwa-mem2": "bwa-mem2",
    "gatk": "brewsci/bio/gatk",
    "blastn": "blast",
    "fastqc": "fastqc",
}


def check_binary(name: str) -> tuple[str, bool, str | None]:
    """Check if a binary exists and get its version."""
    path = shutil.which(name)
    if not path:
        return (name, False, None)
    try:
        result = subprocess.run([name, "--version"], capture_output=True, text=True, timeout=10)
        version = result.stdout.strip().split("\n")[0] if result.returncode == 0 else None
        return (name, True, version)
    except Exception:
        return (name, True, None)


def detect_os() -> str:
    """Detect the operating system."""
    system = platform.system()
    if system == "Darwin":
        return "macos"
    elif system == "Linux":
        return "linux"
    return "unknown"


def install_via_brew(package: str) -> bool:
    """Install a package via Homebrew."""
    try:
        result = subprocess.run(["brew", "install", package], capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception:
        return False
```

- [ ] **Step 3: Run test and verify it passes**

Run: `pytest tests/unit/test_cli.py::test_check_binary_returns_tuple -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add genomix/project/setup_wizard.py tests/unit/test_cli.py
git commit -m "feat: add setup wizard with binary detection and brew install"
```

---

## Task 16: Swarm Manager

**Files:**
- Create: `genomix/swarm/__init__.py`
- Create: `genomix/swarm/manager.py`
- Create: `tests/unit/test_swarm_manager.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_swarm_manager.py`:
```python
import json
from pathlib import Path

import pytest

from genomix.swarm.manager import SwarmManager, SwarmTask, TaskStatus


def test_submit_task(tmp_path):
    """submit() creates a tracked task."""
    sm = SwarmManager(state_dir=tmp_path)
    task = sm.submit(command="/align", args=["data/sample.fastq.gz"])
    assert task.status == TaskStatus.PENDING
    assert task.command == "/align"


def test_list_tasks(tmp_path):
    """list_tasks() returns all tasks."""
    sm = SwarmManager(state_dir=tmp_path)
    sm.submit(command="/qc", args=["data/reads.fastq"])
    sm.submit(command="/blast", args=["data/query.fasta"])
    tasks = sm.list_tasks()
    assert len(tasks) == 2


def test_task_state_persisted(tmp_path):
    """Task state is saved to disk as JSON."""
    sm = SwarmManager(state_dir=tmp_path)
    task = sm.submit(command="/align", args=["x.fastq"])
    state_file = tmp_path / f"{task.id}.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert data["command"] == "/align"


def test_cancel_task(tmp_path):
    """cancel() sets task status to CANCELLED."""
    sm = SwarmManager(state_dir=tmp_path)
    task = sm.submit(command="/qc", args=[])
    sm.cancel(task.id)
    updated = sm.get_task(task.id)
    assert updated.status == TaskStatus.CANCELLED
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_swarm_manager.py -v`
Expected: FAIL

- [ ] **Step 3: Implement swarm manager**

Create `genomix/swarm/__init__.py` (empty).

Create `genomix/swarm/manager.py`:
```python
"""Swarm manager: track background analyses."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
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
    """Manage background analysis tasks."""

    def __init__(self, state_dir: Path, max_concurrent: int = 4):
        self.state_dir = state_dir
        self.max_concurrent = max_concurrent
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def submit(self, command: str, args: list[str]) -> SwarmTask:
        """Create a new task."""
        task = SwarmTask(
            id=uuid.uuid4().hex[:8],
            command=command,
            args=args,
        )
        self._save(task)
        return task

    def list_tasks(self) -> list[SwarmTask]:
        """List all tracked tasks."""
        tasks = []
        for f in sorted(self.state_dir.glob("*.json")):
            tasks.append(self._load(f))
        return tasks

    def get_task(self, task_id: str) -> SwarmTask | None:
        """Get a task by ID."""
        path = self.state_dir / f"{task_id}.json"
        if not path.exists():
            return None
        return self._load(path)

    def cancel(self, task_id: str) -> None:
        """Cancel a task."""
        task = self.get_task(task_id)
        if task:
            task.status = TaskStatus.CANCELLED
            self._save(task)

    def update(self, task_id: str, **kwargs: Any) -> None:
        """Update task fields."""
        task = self.get_task(task_id)
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            self._save(task)

    def _save(self, task: SwarmTask) -> None:
        path = self.state_dir / f"{task.id}.json"
        data = {
            "id": task.id,
            "command": task.command,
            "args": task.args,
            "status": task.status.value,
            "pid": task.pid,
            "progress": task.progress,
            "output": task.output,
            "error": task.error,
        }
        path.write_text(json.dumps(data, indent=2))

    def _load(self, path: Path) -> SwarmTask:
        data = json.loads(path.read_text())
        return SwarmTask(
            id=data["id"],
            command=data["command"],
            args=data["args"],
            status=TaskStatus(data["status"]),
            pid=data.get("pid"),
            progress=data.get("progress", ""),
            output=data.get("output", ""),
            error=data.get("error", ""),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_swarm_manager.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add genomix/swarm/ tests/unit/test_swarm_manager.py
git commit -m "feat: add swarm manager for background analysis tracking"
```

---

## Task 17: Built-in Skills Content (12 SKILL.md files)

**Files:**
- Create: 12 SKILL.md files in `skills/` directory

- [ ] **Step 1: Create all skill files**

Each skill follows the YAML frontmatter + markdown body format defined in the spec. These are LLM instructions, not code. Write substantive instructions for each that guide the agent's behavior.

Key skills to write (abbreviated — each should be 30-80 lines):

1. `skills/sequencing/quality-control/SKILL.md` — FastQC interpretation, trimming recommendations
2. `skills/sequencing/alignment/SKILL.md` — BWA strategy, paired-end detection, index management
3. `skills/sequencing/variant-calling/SKILL.md` — GATK best practices, germline vs somatic
4. `skills/sequencing/annotation/SKILL.md` — SnpEff/VEP usage, clinical interpretation
5. `skills/comparative/blast-analysis/SKILL.md` — Program selection (blastn/p/x), e-value guidance
6. `skills/comparative/multiple-alignment/SKILL.md` — MAFFT/MUSCLE choice, when to trim
7. `skills/comparative/phylogenetics/SKILL.md` — Tree building, model selection, bootstrapping
8. `skills/exploration/sequence-summary/SKILL.md` — File format detection, key statistics extraction
9. `skills/exploration/database-search/SKILL.md` — NCBI/Ensembl search strategies
10. `skills/exploration/variant-explain/SKILL.md` — Variant explanation for non-specialists
11. `skills/common/file-formats/SKILL.md` — FASTA, FASTQ, BAM, VCF, GFF recognition
12. `skills/common/genome-references/SKILL.md` — Reference genome builds, liftover guidance

- [ ] **Step 2: Verify skills are discoverable**

```python
# Quick check
from genomix.skills.registry import SkillRegistry
from pathlib import Path
reg = SkillRegistry([Path("skills")])
assert len(reg.list_skills()) == 12
```

- [ ] **Step 3: Commit**

```bash
git add skills/
git commit -m "feat: add 12 built-in genomics skills"
```

---

## Task 18: Test Fixtures

**Files:**
- Create: `tests/fixtures/tiny.fasta`
- Create: `tests/fixtures/tiny.fastq`
- Create: `tests/fixtures/tiny.vcf`

- [ ] **Step 1: Create synthetic fixture files**

`tiny.fasta` (2 sequences):
```
>seq1 test sequence 1
ATCGATCGATCGATCGATCG
>seq2 test sequence 2
GCTAGCTAGCTAGCTAGCTA
```

`tiny.fastq` (3 reads):
```
@read1
ATCGATCGATCGATCGATCG
+
FFFFFFFFFFFFFFFFFFFF
@read2
GCTAGCTAGCTAGCTAGCTA
+
FFFFFFFFFFFFFFFFFFFF
@read3
ATATATATATATATATATAT
+
FFFFFFFFFFFFFFFFFFFF
```

`tiny.vcf` (3 variants):
```
##fileformat=VCFv4.2
##source=genomix-test
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chr17	41245466	rs28897696	G	A	100	PASS	.
chr13	32936732	rs80359550	C	T	100	PASS	.
chr7	117559593	rs113993960	ATCT	A	100	PASS	.
```

- [ ] **Step 2: Commit**

```bash
git add tests/fixtures/
git commit -m "feat: add synthetic test fixtures (FASTA, FASTQ, VCF)"
```

---

## Task 19: OpenAI and OpenCode Providers

**Files:**
- Create: `genomix/providers/openai_provider.py`
- Create: `genomix/providers/opencode.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/test_provider_base.py`:
```python
def test_get_provider_openai():
    from genomix.providers.openai_provider import OpenAIProvider
    provider = get_provider("openai", api_key="test", model="gpt-4o")
    assert isinstance(provider, OpenAIProvider)


def test_get_provider_opencode():
    from genomix.providers.opencode import OpenCodeProvider
    provider = get_provider("opencode", endpoint="http://localhost:11434", model="llama3.3:70b")
    assert isinstance(provider, OpenCodeProvider)
```

- [ ] **Step 2: Implement both providers**

`openai_provider.py` — same pattern as Claude but using the `openai` SDK.

`opencode.py` — uses `httpx` to call Ollama's OpenAI-compatible API at the configured endpoint.

Both implement `BaseProvider.chat()`, `supports_tool_calling()`, `max_context_length()`.

- [ ] **Step 3: Run tests, verify pass**

Run: `pytest tests/unit/test_provider_base.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add genomix/providers/openai_provider.py genomix/providers/opencode.py tests/unit/test_provider_base.py
git commit -m "feat: add OpenAI and OpenCode (Ollama) providers"
```

---

## Task 20: Context Compressor

**Files:**
- Create: `genomix/agent/context_compressor.py`
- Create: `tests/unit/test_context_compressor.py` (extend `test_agent_loop.py` or new file)

- [ ] **Step 1: Write failing test**

```python
from genomix.agent.context_compressor import should_compress, compress_messages


def test_should_compress_under_limit():
    messages = [{"role": "user", "content": "Hi"}]
    assert should_compress(messages, max_tokens=200_000) is False


def test_should_compress_over_limit():
    big = [{"role": "tool", "content": "x" * 100_000}] * 5
    assert should_compress(big, max_tokens=200_000) is True


def test_compress_preserves_recent():
    messages = [
        {"role": "system", "content": "You are Genomix"},
        {"role": "user", "content": "old question"},
        {"role": "assistant", "content": "old answer"},
        {"role": "tool", "content": "x" * 50_000, "tool_call_id": "c1"},
        {"role": "user", "content": "new question"},
    ]
    compressed = compress_messages(messages, max_tokens=1000)
    # System and recent user message preserved
    assert compressed[0]["role"] == "system"
    assert compressed[-1]["content"] == "new question"
    # Old tool result should be summarized
    assert len(compressed) <= len(messages)
```

- [ ] **Step 2: Implement context compressor**

```python
"""Context compression: summarize old tool results when context grows."""

from __future__ import annotations

from typing import Any

# Rough estimation: 1 token ≈ 4 chars
CHARS_PER_TOKEN = 4


def estimate_tokens(messages: list[dict[str, Any]]) -> int:
    total = 0
    for m in messages:
        content = m.get("content", "")
        if content:
            total += len(content) // CHARS_PER_TOKEN
    return total


def should_compress(messages: list[dict[str, Any]], max_tokens: int) -> bool:
    return estimate_tokens(messages) > max_tokens * 0.8


def compress_messages(messages: list[dict[str, Any]], max_tokens: int) -> list[dict[str, Any]]:
    """Compress messages by summarizing old tool results."""
    if not should_compress(messages, max_tokens):
        return messages

    result = []
    # Always keep system prompt
    if messages and messages[0]["role"] == "system":
        result.append(messages[0])
        messages = messages[1:]

    # Keep last 6 messages intact (recent context)
    keep_recent = min(6, len(messages))
    old = messages[:-keep_recent] if keep_recent < len(messages) else []
    recent = messages[-keep_recent:]

    # Summarize old tool results
    for msg in old:
        if msg.get("role") == "tool" and len(msg.get("content", "")) > 500:
            msg = {**msg, "content": msg["content"][:200] + "\n... [truncated]"}
        result.append(msg)

    result.extend(recent)
    return result
```

- [ ] **Step 3: Run tests, verify pass**

- [ ] **Step 4: Commit**

```bash
git add genomix/agent/context_compressor.py tests/unit/
git commit -m "feat: add context compressor for long conversations"
```

---

## Task 21: Final Integration & README

**Files:**
- Modify: `genomix/cli.py` — final wiring
- Create: `README.md`

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass

- [ ] **Step 2: Write README.md**

Include: project description, installation, quickstart, slash commands reference, contributing guide, license.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete MVP — README and final integration"
```

- [ ] **Step 4: Create GitHub repository**

```bash
gh repo create genomix-cli --public --description "AI-powered CLI for DNA sequence and genome analysis" --license apache-2.0
git remote add origin <url>
git push -u origin main
```

---

## Task 22: Non-Interactive Mode (genomix run / genomix ask)

**Files:**
- Modify: `genomix/cli.py`
- Create: `tests/unit/test_cli_noninteractive.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_cli_noninteractive.py`:
```python
from unittest.mock import patch, MagicMock

from genomix.cli import handle_run, handle_ask


def test_handle_run_calls_agent_with_skill(tmp_path):
    """genomix run /qc loads the skill and runs the agent."""
    with patch("genomix.cli.create_agent_loop") as mock_create:
        mock_loop = MagicMock()
        mock_loop.chat.return_value = "QC complete"
        mock_create.return_value = mock_loop
        result = handle_run("/qc", args=["data/reads.fastq"], output_format="text")
        assert mock_loop.chat.called


def test_handle_ask_passes_question_to_agent():
    """genomix ask sends the question to the agent and returns the response."""
    with patch("genomix.cli.create_agent_loop") as mock_create:
        mock_loop = MagicMock()
        mock_loop.chat.return_value = "42 variants"
        mock_create.return_value = mock_loop
        result = handle_ask("How many variants in sample1.vcf?")
        assert result == "42 variants"


def test_handle_run_json_format():
    """genomix run --format json wraps output in JSON."""
    with patch("genomix.cli.create_agent_loop") as mock_create:
        mock_loop = MagicMock()
        mock_loop.chat.return_value = "Done"
        mock_create.return_value = mock_loop
        result = handle_run("/qc", args=[], output_format="json")
        assert '"response"' in result or '"result"' in result
```

- [ ] **Step 2: Implement handle_run and handle_ask in cli.py**

```python
def create_agent_loop(skill_path: str | None = None) -> AgentLoop:
    """Factory to create a wired agent loop."""
    config = load_config()
    secrets = load_secrets()
    provider = get_provider(config.provider, api_key=secrets.get(f"{config.provider}_api_key", ""), model=config.model)
    registry = ToolRegistry()
    register_file_tools(registry)
    project = None
    try:
        project = ProjectManager.discover(Path.cwd())
    except ProjectNotFoundError:
        pass
    skill_body = None
    if skill_path:
        skill_registry = SkillRegistry([Path(__file__).parent.parent / "skills"])
        skill = skill_registry.get_skill_by_path(skill_path)
        if skill:
            skill_body = skill.body
    privacy = config.privacy_mode or config.provider == "opencode"
    system_prompt = build_system_prompt(project=project, skill_body=skill_body, privacy_mode=privacy)
    return AgentLoop(provider=provider, tool_registry=registry, system_prompt=system_prompt)


def handle_run(slash_command: str, args: list[str], output_format: str = "text") -> str:
    skill_path = COMMAND_SKILL_MAP.get(slash_command)
    loop = create_agent_loop(skill_path=skill_path)
    message = f"{slash_command} {' '.join(args)}".strip()
    result = loop.chat(message)
    if output_format == "json":
        import json
        return json.dumps({"command": slash_command, "response": result})
    return result


def handle_ask(question: str) -> str:
    loop = create_agent_loop()
    return loop.chat(question)
```

Wire into `main()`:
```python
if args.command == "run":
    print(handle_run(args.slash_command, args.args or [], args.format))
elif args.command == "ask":
    question = " ".join(args.question) if args.question else sys.stdin.read().strip()
    print(handle_ask(question))
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `pytest tests/unit/test_cli_noninteractive.py -v`
Expected: 3 PASS

- [ ] **Step 4: Commit**

```bash
git add genomix/cli.py tests/unit/test_cli_noninteractive.py
git commit -m "feat: add non-interactive mode (genomix run / genomix ask)"
```

---

## Task 23: Session History (SQLite + FTS5)

**Files:**
- Create: `genomix/agent/session_store.py`
- Create: `tests/unit/test_session_store.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_session_store.py`:
```python
import pytest
from genomix.agent.session_store import SessionStore


def test_save_and_load_session(tmp_path):
    db_path = tmp_path / "sessions.db"
    store = SessionStore(db_path)
    messages = [
        {"role": "user", "content": "What is BRCA1?"},
        {"role": "assistant", "content": "BRCA1 is a tumor suppressor gene."},
    ]
    session_id = store.save_session(messages, title="BRCA1 inquiry")
    loaded = store.load_session(session_id)
    assert len(loaded) == 2
    assert loaded[0]["content"] == "What is BRCA1?"


def test_search_sessions(tmp_path):
    db_path = tmp_path / "sessions.db"
    store = SessionStore(db_path)
    store.save_session([{"role": "user", "content": "Tell me about TP53"}], title="TP53")
    store.save_session([{"role": "user", "content": "Align my reads"}], title="Alignment")
    results = store.search("TP53")
    assert len(results) == 1
    assert "TP53" in results[0]["title"]


def test_list_sessions(tmp_path):
    db_path = tmp_path / "sessions.db"
    store = SessionStore(db_path)
    store.save_session([{"role": "user", "content": "q1"}], title="Session 1")
    store.save_session([{"role": "user", "content": "q2"}], title="Session 2")
    sessions = store.list_sessions()
    assert len(sessions) == 2
```

- [ ] **Step 2: Implement session store**

Create `genomix/agent/session_store.py`:
```python
"""Session history storage with SQLite + FTS5."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SessionStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    messages TEXT,
                    created_at TEXT
                )
            """)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts
                USING fts5(id, title, content)
            """)

    def save_session(self, messages: list[dict[str, Any]], title: str = "") -> str:
        session_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc).isoformat()
        content = " ".join(m.get("content", "") for m in messages if m.get("content"))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, messages, created_at) VALUES (?, ?, ?, ?)",
                (session_id, title, json.dumps(messages), now),
            )
            conn.execute(
                "INSERT INTO sessions_fts (id, title, content) VALUES (?, ?, ?)",
                (session_id, title, content),
            )
        return session_id

    def load_session(self, session_id: str) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT messages FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            return []
        return json.loads(row[0])

    def search(self, query: str) -> list[dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, title FROM sessions_fts WHERE sessions_fts MATCH ?", (query,)
            ).fetchall()
        return [{"id": r[0], "title": r[1]} for r in rows]

    def list_sessions(self, limit: int = 20) -> list[dict[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, title, created_at FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [{"id": r[0], "title": r[1], "created_at": r[2]} for r in rows]
```

- [ ] **Step 3: Run tests, verify pass**

Run: `pytest tests/unit/test_session_store.py -v`
Expected: 3 PASS

- [ ] **Step 4: Commit**

```bash
git add genomix/agent/session_store.py tests/unit/test_session_store.py
git commit -m "feat: add session history storage with SQLite FTS5"
```

---

## Task 24: Output Naming & Error Classification

**Files:**
- Create: `genomix/output.py`
- Create: `genomix/errors.py`
- Create: `tests/unit/test_output.py`
- Create: `tests/unit/test_errors.py`

- [ ] **Step 1: Write failing tests for output naming**

Create `tests/unit/test_output.py`:
```python
from genomix.output import output_path_for


def test_output_path_qc():
    path = output_path_for("/qc", input_file="data/raw/sample1_R1.fastq.gz", project_root="/proj")
    assert path.endswith("reports/sample1_R1_fastqc.html") or "reports" in path


def test_output_path_align():
    path = output_path_for("/align", input_file="data/raw/sample1_R1.fastq.gz", project_root="/proj")
    assert "sample1_R1.sorted.bam" in path
    assert "data/processed" in path


def test_output_path_variant_call():
    path = output_path_for("/variant-call", input_file="data/processed/sample1.sorted.bam", project_root="/proj")
    assert "sample1.vcf.gz" in path


def test_output_path_override():
    path = output_path_for("/align", input_file="x.fastq", project_root="/proj", override="/custom/out.bam")
    assert path == "/custom/out.bam"
```

Create `tests/unit/test_errors.py`:
```python
from genomix.errors import classify_error, GenomixErrorClass


def test_classify_missing_tool():
    err = classify_error("FileNotFoundError: [Errno 2] No such file or directory: 'bwa'")
    assert err.error_class == GenomixErrorClass.MISSING_TOOL


def test_classify_bad_input():
    err = classify_error("truncated file: data/corrupt.fastq")
    assert err.error_class == GenomixErrorClass.BAD_INPUT


def test_classify_resource_exhaustion():
    err = classify_error("java.lang.OutOfMemoryError: Java heap space")
    assert err.error_class == GenomixErrorClass.RESOURCE_EXHAUSTION
```

- [ ] **Step 2: Implement output.py and errors.py**

`genomix/output.py`:
```python
"""Deterministic output path generation per spec section 13."""

from __future__ import annotations

import os
from pathlib import Path

OUTPUT_MAP = {
    "/qc": ("reports", "{sample}_fastqc.html"),
    "/align": ("data/processed", "{sample}.sorted.bam"),
    "/variant-call": ("data/processed", "{sample}.vcf.gz"),
    "/annotate": ("data/processed", "{sample}.annotated.vcf.gz"),
    "/blast": ("data/processed", "{sample}_blast_results.tsv"),
    "/msa": ("data/processed", "{sample}_alignment.fasta"),
    "/phylo": ("data/processed", "{sample}_tree.nwk"),
}


def output_path_for(command: str, input_file: str, project_root: str, override: str | None = None) -> str:
    if override:
        return override
    sample = Path(input_file).stem.split(".")[0]  # strip extensions
    entry = OUTPUT_MAP.get(command)
    if not entry:
        return str(Path(project_root) / "data" / "processed" / sample)
    directory, template = entry
    filename = template.format(sample=sample)
    return str(Path(project_root) / directory / filename)
```

`genomix/errors.py`:
```python
"""Error classification for bioinformatics tool failures."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class GenomixErrorClass(str, Enum):
    BAD_INPUT = "bad_input"
    MISSING_TOOL = "missing_tool"
    MISSING_INDEX = "missing_index"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    TOOL_CRASH = "tool_crash"
    API_FAILURE = "api_failure"
    UNKNOWN = "unknown"


@dataclass
class ClassifiedError:
    error_class: GenomixErrorClass
    message: str
    suggestion: str


PATTERNS = [
    (r"No such file or directory.*(?:bwa|samtools|gatk|blastn|fastqc)", GenomixErrorClass.MISSING_TOOL,
     "Run 'genomix setup' to install missing tools."),
    (r"(?:truncated|corrupt|invalid|malformed).*(?:fastq|fasta|bam|vcf)", GenomixErrorClass.BAD_INPUT,
     "Check the input file — it may be corrupted or in the wrong format."),
    (r"(?:No index|\.bai|\.fai|\.idx).*not found", GenomixErrorClass.MISSING_INDEX,
     "Generating the missing index automatically..."),
    (r"(?:OutOfMemory|oom|Cannot allocate|disk full|No space left)", GenomixErrorClass.RESOURCE_EXHAUSTION,
     "Try a smaller region (--intervals) or increase available memory."),
    (r"(?:Segmentation fault|core dumped|SIGKILL|SIGSEGV)", GenomixErrorClass.TOOL_CRASH,
     "The tool crashed. Try updating it or use an alternative."),
    (r"(?:rate limit|429|timeout|ConnectionError|HTTPError)", GenomixErrorClass.API_FAILURE,
     "API request failed. Retrying with backoff..."),
]


def classify_error(error_text: str) -> ClassifiedError:
    for pattern, error_class, suggestion in PATTERNS:
        if re.search(pattern, error_text, re.IGNORECASE):
            return ClassifiedError(error_class=error_class, message=error_text, suggestion=suggestion)
    return ClassifiedError(error_class=GenomixErrorClass.UNKNOWN, message=error_text, suggestion="Check the error message above.")
```

- [ ] **Step 3: Run tests, verify pass**

Run: `pytest tests/unit/test_output.py tests/unit/test_errors.py -v`
Expected: 7 PASS

- [ ] **Step 4: Commit**

```bash
git add genomix/output.py genomix/errors.py tests/unit/test_output.py tests/unit/test_errors.py
git commit -m "feat: add output naming contracts and error classification"
```

---

## Task 25: Wire Session Commands (/swarm, /history, /provider, /model, /pipeline)

**Files:**
- Modify: `genomix/cli.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/test_cli.py`:
```python
def test_handle_slash_swarm(tmp_path):
    """The /swarm command lists swarm tasks."""
    from genomix.swarm.manager import SwarmManager
    sm = SwarmManager(state_dir=tmp_path)
    sm.submit(command="/align", args=["x.fastq"])
    # Verify the swarm has tasks to show
    assert len(sm.list_tasks()) == 1
```

- [ ] **Step 2: Implement session command handlers in the interactive loop**

Add handlers to the interactive loop's command dispatch:
- `/swarm` → calls `SwarmManager.list_tasks()` and displays table
- `/swarm cancel <id>` → calls `SwarmManager.cancel(id)`
- `/history` → calls `SessionStore.list_sessions()` and displays
- `/history search <query>` → calls `SessionStore.search(query)`
- `/provider <name>` → updates in-memory config, reconstructs provider
- `/model <name>` → updates in-memory config model
- `/pipeline <files>` → chains `/qc` → `/align` → `/variant-call` → `/annotate` sequentially via agent

- [ ] **Step 3: Run tests, verify pass**

- [ ] **Step 4: Commit**

```bash
git add genomix/cli.py tests/unit/test_cli.py
git commit -m "feat: wire /swarm, /history, /provider, /model, /pipeline commands"
```

---

## Task 26: MCP Lifecycle & Privacy Auto-Activation

**Files:**
- Modify: `genomix/tools/mcp_bridge.py` — add lazy-start, reconnection with backoff
- Modify: `genomix/cli.py` — auto-activate privacy when provider is opencode
- Modify: `genomix/config.py` — set secrets.yaml to mode 0600 on creation

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/test_mcp_bridge.py`:
```python
import asyncio

def test_lazy_connect_on_first_dispatch():
    """Server connects lazily on first tool dispatch, not at registration."""
    bridge = MCPBridge()
    config = MCPServerConfig(name="test", command="python", args=[], enabled=True)
    bridge.register_server(config)
    assert "test" not in bridge._connections  # Not connected yet
```

Add to `tests/unit/test_config.py`:
```python
import os
import stat

from genomix.config import save_secrets


def test_save_secrets_sets_permissions(tmp_path):
    """save_secrets creates file with mode 0600."""
    secrets_path = tmp_path / "secrets.yaml"
    save_secrets({"api_key": "test"}, secrets_path=secrets_path)
    mode = oct(stat.S_IMODE(os.stat(secrets_path).st_mode))
    assert mode == "0o600"
```

- [ ] **Step 2: Implement changes**

In `mcp_bridge.py`, add `_ensure_connected(server_name)` called by dispatch — lazy-starts on first use. Add retry with exponential backoff (1s, 2s, 4s — max 3 retries).

In `config.py`, add `save_secrets(data, secrets_path)` that writes YAML and `os.chmod(path, 0o600)`.

In `cli.py`'s `create_agent_loop()`, auto-set `privacy_mode=True` when provider is `opencode`.

- [ ] **Step 3: Run tests, verify pass**

- [ ] **Step 4: Commit**

```bash
git add genomix/tools/mcp_bridge.py genomix/config.py genomix/cli.py tests/unit/
git commit -m "feat: add MCP lazy-start, secrets permissions, privacy auto-activation"
```

---

## Task 27: Add Missing BLAST Tools (blastx, tblastn)

**Files:**
- Modify: `mcp_servers/biotools/blast_server.py`

- [ ] **Step 1: Add blastx and tblastn tools**

```python
_blastx = BaseBiotoolServer(binary_name="blastx")
_tblastn = BaseBiotoolServer(binary_name="tblastn")


@mcp.tool()
def blastx(query_fasta: str, database: str, evalue: str = "1e-5", max_target_seqs: int = 10, outfmt: str = "6") -> str:
    """Search translated nucleotide sequences against a protein database."""
    return _blastx.run_command([
        "-query", query_fasta, "-db", database,
        "-evalue", evalue, "-max_target_seqs", str(max_target_seqs), "-outfmt", outfmt,
    ])


@mcp.tool()
def tblastn(query_fasta: str, database: str, evalue: str = "1e-5", max_target_seqs: int = 10, outfmt: str = "6") -> str:
    """Search protein sequences against a translated nucleotide database."""
    return _tblastn.run_command([
        "-query", query_fasta, "-db", database,
        "-evalue", evalue, "-max_target_seqs", str(max_target_seqs), "-outfmt", outfmt,
    ])
```

- [ ] **Step 2: Commit**

```bash
git add mcp_servers/biotools/blast_server.py
git commit -m "feat: add blastx and tblastn to BLAST MCP server"
```
