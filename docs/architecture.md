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

### Streaming (`genomix/tui_renderer.py`)
Responses stream token-by-token via `StreamEvent` typed objects:
- `TextDelta` — text fragment from LLM
- `ToolCallStart/Complete` — tool invocation events
- `ToolResult` — tool execution result
- `StreamDone` — end of response

The `StreamingRenderer` displays raw text as it streams, then re-renders as Markdown on completion. A thinking spinner shows before the first token arrives.

### Clinical Reports (`genomix/report.py`)
The `/report` command generates styled HTML reports from VCF files:
1. LLM analyzes variants and returns structured JSON
2. Interpretation and recommendations auto-generated from variant data
3. HTML rendered with ACMG significance badges
4. Saved to `reports/` directory

### Structural Biology Integration
AlphaFold, UniProt, PDB, and InterPro servers enable protein structure analysis:
- Gene → UniProt accession resolution
- AlphaFold pLDDT confidence at variant positions
- AlphaMissense pathogenicity predictions for missense variants
- Protein domain mapping via InterPro
- Experimental structure lookup via RCSB PDB

Variant analysis skills (v2.0) automatically include structural context when analyzing missense variants.

## Data Flow

### Interactive (streaming)
```
1. User types question or /command
2. TUI loads skill (if applicable)
3. Agent loop builds context (system prompt + project + skill + history)
4. Provider streams response → yields StreamEvents
5. Agent loop accumulates tool calls, dispatches via registry
6. Tool results fed back to provider for next iteration
7. StreamingRenderer shows text progressively, re-renders as Markdown on done
```

### Non-interactive
```
genomix ask "question" → Agent loop → chat() → accumulates text → prints
genomix run /qc file.fq → loads skill → Agent loop → prints result
```

## Key Design Decisions

- **MCP over direct subprocess** — standardized tool interface, hot-swappable
- **Streaming events** — typed dataclasses flow provider → loop → renderer
- **Context compression** — auto-truncates old tool results when approaching token limit
- **Privacy mode** — auto-active with local models, raw sequences never sent to cloud
- **Skills as markdown** — non-developers can contribute domain expertise
