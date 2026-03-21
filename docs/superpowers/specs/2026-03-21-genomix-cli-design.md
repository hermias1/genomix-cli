# Genomix CLI — Design Specification

**Date:** 2026-03-21
**Status:** Approved
**License:** Apache 2.0
**Package name:** `genomix-cli`
**CLI command:** `genomix`

---

## 1. Vision

Genomix CLI is an open-source, AI-powered command-line tool for DNA sequence and genome analysis. It acts as an intelligent orchestrator: the user asks questions or triggers commands in natural language, and the AI selects and runs the right bioinformatics tools, queries the right databases, and explains results in accessible language.

**Inspired by** OpenGauss (multi-agent Lean proof assistant) — same architectural patterns (project-scoped, skills, MCP tools, swarm), applied to genomics.

## 2. Target Audience (priority order)

1. **Biologists / geneticists** — non-coders who want to analyze genomic data via natural language
2. **Bioinformaticians** — experts who want AI-assisted orchestration of their existing tools
3. **Developers / data scientists** — integrating genomic analysis into pipelines

## 3. Scope

### MVP (Phase 1)

- **A) DNA Sequencing / Variants** — FASTA, FASTQ, BAM, VCF — alignment, variant calling, annotation (classic NGS pipeline)
- **B) Comparative Genomics** — BLAST, multiple sequence alignment, phylogenetics

### Future (Phase 2+)

- **C) Transcriptomics** — RNA-seq, differential expression
- **D) Functional Genomics** — gene annotation, protein prediction, functional domains

## 4. Tech Stack

- **Language:** Python (CLI + orchestration)
- **Heavy lifting:** External binaries (samtools, BWA, GATK, BLAST+, etc.) called via MCP servers / subprocess
- **AI Provider:** Claude via Anthropic API (default) | OpenAI API/GPT-4o (alternative) | OpenCode via Ollama (local/confidential)
- **CLI framework:** prompt_toolkit (interactive TUI + non-interactive/pipe mode for scripting)
- **MCP protocol:** MCP 2025-03 (stdio transport for local biotools, HTTP/SSE for remote databases)
- **Distribution:** `pip install genomix-cli` + `genomix setup` wizard
- **License:** Apache 2.0

## 5. Architecture

```
┌─────────────────────────────────────────────────────┐
│                   genomix-cli                        │
│                                                      │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ CLI/TUI   │  │  Agent    │  │  Swarm Manager   │  │
│  │ (prompt_  │──│  Loop     │──│  (background     │  │
│  │  toolkit) │  │  (LLM)   │  │   analyses)      │  │
│  └───────────┘  └────┬─────┘  └──────────────────┘  │
│                      │                                │
│         ┌────────────┼────────────┐                   │
│         ▼            ▼            ▼                   │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐            │
│  │ Tool     │ │ Skills   │ │ Project   │            │
│  │ Registry │ │ System   │ │ Manager   │            │
│  └────┬─────┘ └──────────┘ └───────────┘            │
│       │                                               │
│       ▼                                               │
│  ┌──────────────────────────────────────┐            │
│  │          MCP Servers Layer           │            │
│  │  biotools: samtools, bcftools, BWA,  │            │
│  │    GATK, FreeBayes, BLAST+, MAFFT,  │            │
│  │    FastTree, FastQC, SnpEff, VEP    │            │
│  │  databases: NCBI, Ensembl, ClinVar, │            │
│  │    dbSNP, UniProt, UCSC, COSMIC, PDB│            │
│  └──────────────────────────────────────┘            │
│                                                       │
│  ┌──────────────────────────────────────┐            │
│  │       AI Provider Abstraction        │            │
│  │  Claude │ OpenAI │ OpenCode (local)  │            │
│  └──────────────────────────────────────┘            │
└───────────────────────────────────────────────────────┘
```

### 6 core components

1. **CLI/TUI** — Interactive interface (prompt_toolkit), slash commands, autocompletion
2. **Agent Loop** — Conversational LLM loop with tool calling
3. **Swarm Manager** — Background analysis tracking (long-running alignments, BLAST, etc.)
4. **Tool Registry** — Centralized tool registration (local + MCP discovery)
5. **Skills System** — Specialized LLM instructions in SKILL.md format
6. **Project Manager** — Project context management (`.genomix/project.yaml`)

## 6. Project Structure (`.genomix/`)

```
project-dir/
├── .genomix/
│   ├── project.yaml          # Project manifest
│   ├── config.yaml            # Local config (provider, model...)
│   ├── runtime/
│   │   ├── sessions.db        # Session history (SQLite + FTS5)
│   │   └── swarm/             # Running analysis state
│   ├── cache/
│   │   ├── references/        # Downloaded reference genomes
│   │   └── databases/         # NCBI/Ensembl query cache
│   └── skills/                # User custom skills
├── data/
│   ├── raw/                   # Raw files (FASTQ, FASTA...)
│   └── processed/             # Results (BAM, VCF, annotations...)
└── reports/                   # Generated reports (QC, summaries...)
```

### `project.yaml`

```yaml
schema_version: 1
name: "BRCA Analysis - Cohort 2026"
organism: "Homo sapiens"
reference_genome: "GRCh38"
data_type: "whole_genome_sequencing"
created_at: "2026-03-21T00:00:00Z"
tools:
  aligner: "bwa-mem2"
  variant_caller: "gatk"
  annotator: "snpeff"
```

### Guided init (for biologists)

```
$ genomix init
🧬 New Genomix Project

Project name: BRCA Analysis - Cohort 2026
Organism: Homo sapiens
Reference genome:
  [1] GRCh38 (Human - recommended)
  [2] GRCh37/hg19 (Human - legacy)
  [3] mm39 (Mouse)
  [4] Other...
> 1

Data type:
  [1] Whole Genome Sequencing (WGS)
  [2] Whole Exome Sequencing (WES)
  [3] Targeted Sequencing (panel)
  [4] Individual sequences (FASTA)
> 1

✓ Project initialized in .genomix/
✓ GRCh38 genome will be downloaded on first alignment
```

## 7. MCP Servers

Each external tool and database = independent MCP server. Users activate what they need.

### Protocol & Transport

- **Protocol:** MCP 2025-03 specification
- **Biotools servers:** stdio transport (spawned as subprocesses by genomix)
- **Database servers:** stdio transport (HTTP calls handled internally by each server)
- **Server lifecycle:** Lazy-started on first tool call, kept alive for session duration, graceful shutdown on exit
- **Discovery:** Servers registered in `.genomix/config.yaml`, auto-discovered at startup
- **Reconnection:** Exponential backoff (max 3 retries) on server crash

### MVP vs Full scope

**MVP (9 servers):** samtools, bwa, gatk, blast, fastqc + ncbi, ensembl, clinvar, dbsnp
**Phase 2 (4 servers):** bcftools, freebayes, snpeff + uniprot
**Phase 3 (6 servers):** mafft, fasttree, vep + ucsc, cosmic, pdb

### Biotools (local binaries)

| Server | Tools exposed | Binary |
|--------|--------------|--------|
| `samtools_server` | view, sort, index, stats, depth, flagstat | samtools |
| `bcftools_server` | view, filter, stats, merge, annotate | bcftools |
| `bwa_server` | mem, index | bwa / bwa-mem2 |
| `gatk_server` | HaplotypeCaller, BaseRecalibrator, MarkDuplicates | gatk |
| `freebayes_server` | call variants | freebayes |
| `blast_server` | blastn, blastp, blastx, tblastn, makeblastdb | blast+ |
| `mafft_server` | align | mafft |
| `fasttree_server` | build tree | fasttree |
| `fastqc_server` | analyze, report | fastqc |
| `snpeff_server` | annotate, dump | snpeff |
| `vep_server` | annotate | vep |

### Databases (remote APIs)

| Server | API | Key data |
|--------|-----|----------|
| `ncbi_server` | Entrez, BLAST API, RefSeq | Sequences, genes, SNPs |
| `ensembl_server` | REST API | Annotated genomes, VEP, variants |
| `clinvar_server` | NCBI E-utils | Clinical variant significance |
| `dbsnp_server` | NCBI E-utils | Known variant catalog |
| `uniprot_server` | REST API | Proteins, functional domains |
| `ucsc_server` | REST API | Reference genomes, annotation tracks |
| `cosmic_server` | REST API | Somatic cancer mutations |
| `pdb_server` | RCSB REST API | 3D protein structures |

### Database integration phases

- **Phase 1 (MVP):** NCBI/GenBank, Ensembl, dbSNP, ClinVar
- **Phase 2:** UniProt, UCSC Genome Browser
- **Phase 3:** COSMIC, PDB

### Configuration

```yaml
# .genomix/config.yaml
mcp_servers:
  samtools:
    enabled: true
    binary_path: auto
  ncbi:
    enabled: true
    email: "user@example.com"    # Required by NCBI
  ensembl:
    enabled: true
  clinvar:
    enabled: true
  cosmic:
    enabled: false
```

### Secrets management

API keys and sensitive credentials are stored in `~/.genomix/secrets.yaml` (user-global, never in project directory). The file is created with `600` permissions. `.genomix/` is added to `.gitignore` by `genomix init`.

```yaml
# ~/.genomix/secrets.yaml (mode 0600)
ncbi_api_key: "abc123..."
anthropic_api_key: "sk-ant-..."
openai_api_key: "sk-..."
cosmic_token: "..."
```

Project-level `config.yaml` references keys by name, never stores them inline.

## 8. Skills System

Skills are specialized LLM instructions in SKILL.md format (YAML frontmatter + markdown). They guide the LLM's reasoning and tool selection — they are not code.

### Built-in skills

```
skills/
├── sequencing/
│   ├── quality-control/SKILL.md
│   ├── alignment/SKILL.md
│   ├── variant-calling/SKILL.md
│   └── annotation/SKILL.md
├── comparative/
│   ├── blast-analysis/SKILL.md
│   ├── multiple-alignment/SKILL.md
│   └── phylogenetics/SKILL.md
├── exploration/
│   ├── sequence-summary/SKILL.md
│   ├── database-search/SKILL.md
│   └── variant-explain/SKILL.md
└── common/
    ├── file-formats/SKILL.md
    └── genome-references/SKILL.md
```

### SKILL.md format

```yaml
---
name: variant-explain
description: Explain a genetic variant in clear, accessible language
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [exploration, education, variants]
    tools_used: [ncbi_snp_info, clinvar_query, ensembl_vep]
---

# Variant Explanation

When the user asks about a specific variant:
1. Identify the variant
2. Locate — chromosome, position, gene, transcript
3. Impact — coding effect, protein change
4. Clinical — ClinVar significance
5. Population — allele frequency
6. Explain — plain language adapted to user's level
```

### Custom skills

Users create their own skills in `.genomix/skills/` following the same format.

## 9. AI Provider Abstraction

```python
class BaseProvider:
    def chat(self, messages, tools) -> Response:
        """Send message, receive response + tool calls."""

    def supports_tool_calling(self) -> bool:
        """Does the provider support native tool calling?"""

    def max_context_length(self) -> int:
        """Max context size (for compression decisions)."""
```

### Providers

| Provider | Backend | Model examples | Use case |
|----------|---------|---------------|----------|
| `claude` | Anthropic API | claude-sonnet-4-6, claude-opus-4-6 | Default — best reasoning |
| `openai` | OpenAI API | gpt-4o, o3 | Alternative, broad ecosystem |
| `opencode` | Ollama (local) | llama3.3:70b, mistral-large | Local execution, confidential/patient data, GDPR compliance |

### Configuration

```yaml
# .genomix/config.yaml
provider:
  default: claude
  model: claude-sonnet-4-6
```

### Privacy mode

Activated automatically when provider is `opencode`, or manually via `/privacy on`.

**What is sent to the LLM:**
- File metadata (name, format, size, record count)
- Aggregated statistics (read count, Q30 score, coverage depth, variant counts)
- Tool output summaries (e.g., "5,423 variants found, 12 in BRCA1")
- Gene/variant identifiers (rs IDs, gene symbols — these are public knowledge)

**What is never sent to the LLM:**
- Raw sequence data (nucleotide strings)
- Patient identifiers or sample metadata
- Full VCF records with genotype calls
- BAM/CRAM read-level data

MCP tools always run 100% locally regardless of provider. Only tool result summaries are passed to the LLM context.

## 10. Slash Commands

### Project

| Command | Description |
|---------|-------------|
| `/project init` | Initialize project (organism, reference genome, data type) |
| `/project info` | Show active project summary |

### Analysis — Sequencing (Case A)

| Command | Description |
|---------|-------------|
| `/qc` | Run quality control (FastQC/MultiQC) |
| `/align` | Align reads to reference genome |
| `/variant-call` | Call variants (GATK/FreeBayes) |
| `/annotate` | Annotate variants (SnpEff/VEP) |
| `/pipeline` | Full pipeline: QC → align → variant-call → annotate |

### Analysis — Comparative (Case B)

| Command | Description |
|---------|-------------|
| `/blast` | BLAST similarity search |
| `/msa` | Multiple sequence alignment |
| `/phylo` | Phylogenetic tree construction |

### Exploration

| Command | Description |
|---------|-------------|
| `/summary` | Summarize a file (FASTA, VCF, BAM...) |
| `/search` | Query databases (NCBI, Ensembl, ClinVar...) |
| `/explain` | Explain a variant, gene, or region |

### Session

| Command | Description |
|---------|-------------|
| `/swarm` | Show running analyses |
| `/history` | Session history |
| `/provider` | Switch AI provider |
| `/model` | Switch model |
| `/help` | Help |

## 11. Agent Loop & UX

### Slash command → skill mapping

Slash commands load their associated skill by convention: `/qc` loads `skills/sequencing/quality-control/SKILL.md`. The mapping is explicit in a registry:

```python
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
```

### Conversation flow

```
User input
    │
    ├── Slash command? → Load mapped skill → Execute with args
    │
    └── Natural language → Agent Loop:
        1. Build context (system prompt + project + relevant skills)
        2. Send to LLM
        3. LLM responds OR requests tool calls
        4. If tool calls → execute via Tool Registry → result to LLM → back to 3
        5. If final response → display to user
            │
            └── Long analysis detected? → Swarm: run in background, notify on completion
```

### Non-interactive mode

For pipeline integration (audience #3), genomix supports piped/scripted usage:

```bash
# Single command, no TUI
genomix run /align data/sample1_R*.fastq.gz --output data/processed/

# Pipe a question
echo "How many variants are in data/processed/sample1.vcf?" | genomix ask

# JSON output for scripting
genomix run /qc data/raw/ --format json
```

### Error handling

Bioinformatics tools fail frequently. Error classes and behavior:

| Error class | Examples | Behavior |
|-------------|----------|----------|
| **Bad input** | Corrupt FASTQ, wrong format | Explain to user, suggest fix |
| **Missing tool** | BWA not installed | Run `genomix setup` suggestion |
| **Missing index** | No .fai for FASTA, no .bai for BAM | Auto-generate index, then retry |
| **Resource exhaustion** | OOM on large genome, disk full | Warn user, suggest smaller region or more resources |
| **Tool crash** | Segfault in external binary | Show stderr, suggest version update or alternative tool |
| **API failure** | NCBI rate limit, network error | Retry with backoff, fallback to cache if available |

The agent always surfaces the original error message and suggests a concrete next step.

### Swarm manager

- **Concurrency model:** multiprocessing (one subprocess per analysis)
- **Max concurrent:** configurable, default 4
- **State:** persisted in `.genomix/runtime/swarm/` as JSON per task
- **Crash recovery:** on CLI restart, detects orphaned processes and reports status
- **Notifications:** terminal bell + inline message when background task completes

### Context compression

When conversation context approaches the LLM's limit:
1. Summarize older tool results (keep conclusions, drop raw output)
2. Preserve: current project context, active analysis state, recent user messages
3. Discard: intermediate tool call details from completed analyses
4. Store full conversation in `sessions.db` for `/history` retrieval

### UX principles

- **Proactive** — suggests next steps, doesn't just answer
- **Adaptive** — detects user level (natural language = biologist, slash commands = expert)
- **Transparent** — always shows what tools it's calling and why
- **Background** — long analyses run via swarm, user keeps interacting

## 12. Repository Structure

```
genomix-cli/
├── LICENSE                        # Apache 2.0
├── README.md
├── pyproject.toml
├── requirements.txt
│
├── genomix/                       # Main package
│   ├── __init__.py
│   ├── cli.py                     # Entry point, TUI
│   ├── config.py                  # Config loading
│   │
│   ├── agent/
│   │   ├── loop.py                # LLM conversation loop + tool calling
│   │   ├── prompt_builder.py      # Contextual system prompt assembly
│   │   └── context_compressor.py  # Context compression
│   │
│   ├── providers/
│   │   ├── base.py
│   │   ├── claude.py
│   │   ├── openai.py
│   │   └── opencode.py
│   │
│   ├── tools/
│   │   ├── registry.py            # Central registry (auto-registration)
│   │   ├── file_tools.py          # Local file operations
│   │   └── mcp_bridge.py          # MCP discovery + dispatch
│   │
│   ├── skills/
│   │   ├── loader.py              # SKILL.md parsing
│   │   └── registry.py            # List, search, progressive disclosure
│   │
│   ├── project/
│   │   ├── manager.py             # Init, discovery, validation
│   │   └── setup_wizard.py        # Guided dependency installation
│   │
│   └── swarm/
│       └── manager.py             # Background analysis tracking
│
├── mcp_servers/
│   ├── biotools/                  # MVP: 5 servers (samtools, bwa, gatk, blast, fastqc)
│   └── databases/                 # MVP: 4 servers (ncbi, ensembl, clinvar, dbsnp)
│
├── skills/                        # 12 built-in skills
│   ├── sequencing/
│   ├── comparative/
│   ├── exploration/
│   └── common/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/                  # Small test FASTA/VCF files
│
└── docs/
    ├── getting-started.md
    ├── skills-guide.md
    └── mcp-servers.md
```

## 13. Output Contracts

Each slash command produces deterministic outputs:

| Command | Output file(s) | Location | Format |
|---------|---------------|----------|--------|
| `/qc` | `{sample}_fastqc.html`, `qc_report.html` | `reports/` | HTML |
| `/align` | `{sample}.sorted.bam`, `{sample}.sorted.bam.bai` | `data/processed/` | BAM |
| `/variant-call` | `{sample}.vcf.gz`, `{sample}.vcf.gz.tbi` | `data/processed/` | VCF |
| `/annotate` | `{sample}.annotated.vcf.gz` | `data/processed/` | VCF |
| `/pipeline` | All of the above | respective dirs | Mixed |
| `/blast` | `{query}_blast_results.tsv` | `data/processed/` | TSV |
| `/msa` | `{name}_alignment.fasta` | `data/processed/` | FASTA |
| `/phylo` | `{name}_tree.nwk` | `data/processed/` | Newick |

Naming convention: `{sample}` derived from input filename. Override with `--output`.

## 14. Installation & Setup

```bash
# Install
pip install genomix-cli

# Setup (guided wizard)
genomix setup
```

### `genomix setup` wizard

Interactive, detects OS, installs missing dependencies:

```
$ genomix setup
🧬 Genomix Setup

Detecting your system... macOS 15.4 (arm64)

Checking required tools:
  ✓ samtools 1.21
  ✗ bwa-mem2 — not found
  ✓ gatk 4.6.1
  ✗ blast+ — not found
  ✓ fastqc 0.12.1

Install missing tools?
  [1] Via Homebrew (recommended on macOS)
  [2] Via Conda/Bioconda
  [3] Skip — I'll install them myself
> 1

Installing bwa-mem2... ✓
Installing blast+... ✓

AI Provider:
  [1] Claude (Anthropic) — recommended
  [2] OpenAI (GPT-4o)
  [3] OpenCode (local via Ollama) — for confidential data
> 1

Enter your Anthropic API key: sk-ant-***
✓ Key saved to ~/.genomix/secrets.yaml

Setup complete! Run 'genomix init' in your project directory to start.
```

**Docker alternative** (for users who can't install binaries):
```bash
docker run -it -v $(pwd):/data genomix-cli/genomix
```

## 15. Testing Strategy

- **Unit tests:** Pure logic (config parsing, skill loading, output naming, format detection). No external binaries needed. Run with `pytest tests/unit/`.
- **Integration tests:** Use small fixture files (`tests/fixtures/` — tiny FASTA/VCF/BAM) and mock MCP server responses. Run with `pytest tests/integration/`. Do NOT require installed binaries — mock subprocess calls.
- **E2E tests:** Require installed binaries. Run separately with `pytest tests/e2e/ --run-e2e`. CI runs these in a Docker container with all tools pre-installed. Skipped by default in local dev.
- **Fixtures:** Small synthetic genomic files (< 1 KB each) — a 10-read FASTQ, a 5-variant VCF, a tiny FASTA.

## 16. Open Questions

- **Visualization:** Terminal-based plots (e.g., coverage plots, variant density)? Or generate HTML reports?
- **Notebook integration:** Should genomix support Jupyter notebook workflows?
- **Web UI:** Future companion web interface, or CLI-only?
- **Plugin marketplace:** Community-contributed MCP servers and skills?
