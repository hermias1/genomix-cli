# Contributing to Genomix CLI

Thanks for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/hermias1/genomix-cli.git
cd genomix-cli

# Create a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e .
pip install pytest

# Run tests
python -m pytest tests/ -v
```

## Project Structure

```
genomix-cli/
├── genomix/                    # Main Python package
│   ├── cli.py                  # Entry point, argument parsing
│   ├── tui.py                  # Interactive terminal UI
│   ├── tui_renderer.py         # Streaming response renderer
│   ├── config.py               # Configuration loading
│   ├── report.py               # HTML report generator
│   ├── errors.py               # Error classification
│   ├── output.py               # Output path naming
│   ├── runtime.py              # Shared utilities
│   ├── agent/                  # AI agent core
│   │   ├── loop.py             # Conversation loop (streaming + non-streaming)
│   │   ├── prompt_builder.py   # System prompt assembly
│   │   ├── context_compressor.py # Context window management
│   │   └── session_store.py    # Session history (SQLite)
│   ├── providers/              # AI provider implementations
│   │   ├── base.py             # BaseProvider ABC + StreamEvent types
│   │   ├── claude.py           # Anthropic Claude
│   │   ├── openai_provider.py  # OpenAI GPT
│   │   └── opencode.py         # Ollama (local)
│   ├── tools/                  # Tool system
│   │   ├── registry.py         # Central tool registry
│   │   ├── file_tools.py       # Built-in file tools
│   │   ├── mcp_bridge.py       # MCP protocol bridge
│   │   └── mcp_manager.py      # MCP server lifecycle
│   ├── skills/                 # Skill loader system
│   │   ├── loader.py           # SKILL.md parser
│   │   └── registry.py         # Skill discovery
│   ├── project/                # Project management
│   │   ├── manager.py          # Init, discover, load projects
│   │   └── setup_wizard.py     # Dependency checker
│   └── swarm/                  # Background analysis
│       └── manager.py          # Task tracking
│
├── mcp_servers/                # MCP server implementations
│   ├── base_biotool.py         # Base class for CLI tool servers
│   ├── base_database.py        # Base class for API servers
│   ├── biotools/               # Local bioinformatics tools
│   │   ├── samtools_server.py
│   │   ├── bwa_server.py
│   │   ├── gatk_server.py
│   │   ├── blast_server.py
│   │   └── fastqc_server.py
│   └── databases/              # Remote database APIs
│       ├── ncbi_server.py
│       ├── ensembl_server.py
│       ├── clinvar_server.py
│       ├── dbsnp_server.py
│       ├── gnomad_server.py
│       ├── omim_server.py
│       ├── pharmgkb_server.py
│       ├── cosmic_server.py
│       ├── interpro_server.py
│       ├── pubmed_server.py
│       ├── alphafold_server.py
│       ├── uniprot_server.py
│       └── pdb_server.py
│
├── skills/                     # Built-in SKILL.md files (21)
│   ├── sequencing/             # NGS pipeline skills
│   ├── comparative/            # Comparative genomics
│   ├── exploration/            # Data exploration
│   ├── clinical/               # (future)
│   ├── oncology/               # Cancer genomics
│   ├── pharmacogenomics/       # Drug interactions
│   ├── reporting/              # Report generation
│   └── structural/             # Protein structure
│
├── tests/                      # Test suite (100 tests)
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
└── docs/                       # Documentation
```

## How to Contribute

### Adding a new MCP Server (database)

This is the easiest way to contribute. Each database server is a self-contained file.

1. Create `mcp_servers/databases/your_server.py`:

```python
"""Your Database MCP server."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("your_db")
_server = BaseDatabaseServer(name="your_db", base_url="https://api.example.com")


@mcp.tool()
def your_db_search(query: str) -> str:
    """Search your database."""
    try:
        result = _server.get("search", {"q": query})
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
```

2. Register in `genomix/tools/mcp_manager.py` — add to `BUILTIN_SERVERS`:

```python
MCPServerInfo(name="your_db", display_name="YourDB", category="databases",
              description="What it does",
              module="mcp_servers.databases.your_server"),
```

3. That's it! The server will auto-connect on startup.

### Adding a new Skill

Skills are markdown files that instruct the AI how to handle specific tasks.

1. Create `skills/category/your-skill/SKILL.md`:

```yaml
---
name: your-skill
description: What this skill does
version: 1.0.0
author: your-name
license: Apache-2.0
metadata:
  genomix:
    tags: [relevant, tags]
    tools_used: [tool_names_it_uses]
---

# Your Skill Title

Instructions for the AI when this skill is active...
```

2. Optionally map to a slash command in `genomix/tui.py`:
   - Add to `SLASH_COMMANDS`
   - Add to `COMMAND_SKILL_MAP`
   - Add to `COMMAND_DESCRIPTIONS`

### Adding a new AI Provider

1. Create `genomix/providers/your_provider.py` implementing `BaseProvider`
2. Add to the factory in `genomix/providers/__init__.py`

### Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/unit/test_config.py -v

# Only unit tests (no external deps)
python -m pytest tests/unit/ -v
```

### Code Style

- Python 3.11+ with type hints
- Keep files focused (one responsibility per file)
- Follow existing patterns — look at similar files before creating new ones
- No unnecessary abstractions

### Pull Requests

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/your-feature`)
3. Write tests first (TDD)
4. Make your changes
5. Run the full test suite
6. Submit a PR with a clear description

## Architecture Overview

```
User Input → CLI/TUI → Agent Loop → Provider (LLM)
                            ↕
                      Tool Registry ← MCP Servers
                            ↕
                      Skills System
```

The agent loop sends messages to the AI provider, which can request tool calls. Tool calls are dispatched through the registry to MCP servers (local biotools or remote database APIs). Skills provide specialized instructions to the AI for specific tasks.

## License

Apache 2.0 — see [LICENSE](LICENSE)
