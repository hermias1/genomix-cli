# Genomix CLI Architecture

## Core Design

Genomix CLI is an AI-powered orchestrator for bioinformatics. It connects an LLM (via streaming) to bioinformatics tools and genomic databases through the MCP (Model Context Protocol).

## Components

### Agent Loop (`genomix/agent/loop.py`)
The conversation engine. Manages message history, streams responses, handles tool call accumulation, and applies context compression.

### Providers (`genomix/providers/`)
AI backend abstraction. Three implementations:
- **OpenCode** (Ollama) — local, default, privacy-friendly
- **Claude** (Anthropic) — best reasoning
- **OpenAI** — alternative

All support streaming via `chat_stream()` which yields `StreamEvent` objects.

### Tool Registry (`genomix/tools/registry.py`)
Central dispatcher for all tools. Stores OpenAI-format schemas and callable handlers. MCP server tools are registered here at startup.

### MCP Servers (`mcp_servers/`)
Each bioinformatics tool or database is wrapped as an MCP server:
- **Biotools** — subprocess wrappers for samtools, BWA, GATK, BLAST, FastQC
- **Databases** — HTTP clients for NCBI, Ensembl, ClinVar, gnomAD, AlphaFold, etc.

Servers are managed by `MCPManager` which handles lifecycle (connect, disconnect, health checks).

### Skills (`skills/`)
Markdown files with YAML frontmatter that provide specialized instructions to the LLM. Skills are loaded on demand when slash commands are invoked.

### TUI (`genomix/tui.py` + `tui_renderer.py`)
Interactive terminal interface using prompt_toolkit (input) and Rich (output). The `StreamingRenderer` displays responses progressively with paragraph-by-paragraph markdown rendering.

## Data Flow

```
1. User types question or /command
2. TUI resolves command → loads skill (if applicable)
3. Agent loop builds context (system prompt + project + skill + history)
4. Provider streams response (TextDelta, ToolCallStart, ToolCallArgs, StreamDone)
5. Agent loop accumulates tool calls, dispatches via registry
6. Tool results fed back to provider for next iteration
7. StreamingRenderer displays everything progressively
```

## Key Design Decisions

- **MCP over direct subprocess** — standardized tool interface, hot-swappable
- **Streaming events** — typed dataclasses flow provider → loop → renderer
- **Context compression** — auto-truncates old tool results when approaching token limit
- **Privacy mode** — auto-active with local models, raw sequences never sent to cloud
- **Skills as markdown** — non-developers can contribute domain expertise
