# Genomix CLI


**AI-powered CLI for DNA sequence and genome analysis.**

<p align="center">
  <img src="docs/demo.svg" alt="Genomix CLI Demo" width="800">
</p>

Genomix is an intelligent command-line tool that helps biologists, bioinformaticians, and researchers analyze genomic data through natural language. Ask questions about your VCF, FASTA, or FASTQ files — the AI reads them, queries real databases (NCBI, Ensembl, ClinVar), and explains results in accessible language.

**Local-first.** Runs with Ollama by default — your genomic data never leaves your machine.

## What It Does

```
❯ Read raw_variants.vcf and give me a clinical summary

  ⚡ read_file(path='raw_variants.vcf')
    ↳ ##fileformat=VCFv4.2 ...

  1. BRCA1 missense (chr17:43094464): Pathogenic — increased breast/ovarian cancer risk
  2. CFTR deletion (chr7:117559593): Pathogenic — cystic fibrosis (homozygous)
  3. HBB missense (chr11:5226773): Pathogenic — sickle cell trait (carrier)
  4. APOE missense (chr19:44908822): Risk factor — Alzheimer's disease
  ...

❯ What does this reveal about the person's ancestry?

  Based on the variant profile:
  - HBB/rs334 (sickle cell trait): high frequency in African/Mediterranean populations
  - CFTR deltaF508: most common in Northern European populations
  - Combined profile suggests mixed European/African ancestry
```

## Features

- **Natural language interface** — ask questions about your genomic data in plain English or French
- **9 MCP servers** — samtools, BWA, GATK, BLAST+, FastQC, NCBI, Ensembl, ClinVar, dbSNP
- **Smart analysis** — reads raw VCFs (no annotations needed), identifies genes from coordinates, infers clinical significance
- **Ancestry inference** — population frequency analysis via gnomAD/1000 Genomes
- **12 built-in skills** — specialized AI instructions for sequencing, comparative genomics, and exploration workflows
- **3 AI providers** — Ollama/local (default), Claude (Anthropic), OpenAI
- **Privacy mode** — automatically active with local models, raw sequences never sent to cloud
- **Slash commands** — `/qc`, `/align`, `/variant-call`, `/blast`, `/msa`, `/explain`, and more
- **MCP management** — `/mcp` to view, connect, and manage bioinformatics tool servers

## Installation

```bash
# Install
pip install genomix-cli

# Check dependencies
genomix setup

# Initialize a project
cd my-analysis/
genomix init
```

### Requirements

- Python 3.11+
- [Ollama](https://ollama.ai) with a model (e.g., `ollama pull qwen3-coder:30b`)
- Optional: samtools, BWA, GATK, BLAST+ for bioinformatics tools

## Quick Start

```bash
# Start interactive mode
genomix

# Non-interactive usage
genomix ask "What is the BRCA1 gene?"
genomix ask "Read sample.vcf and summarize the variants"
genomix run /qc data/reads.fastq.gz
```

### Interactive Session

```
   ██████╗ ███████╗███╗   ██╗ ██████╗ ███╗   ███╗██╗██╗  ██╗
  ...
  v0.1.0 — AI-powered genome analysis

  ┌──────────────────────────────────────────────────────┐
  │  Project    BRCA Analysis - Cohort 2026              │
  │  Organism   Homo sapiens                             │
  │  Reference  GRCh38                                   │
  │  Provider   opencode (qwen3-coder:30b)               │
  │  Privacy    🔒 ON                                    │
  │  MCP        9 registered (4 connected, 5 missing)    │
  └──────────────────────────────────────────────────────┘

  Connecting MCP servers...
  Connecting to ClinVar... ✓ (3 tools)
  Connecting to dbSNP... ✓ (3 tools)
  Connecting to Ensembl... ✓ (5 tools)
  Connecting to NCBI... ✓ (4 tools)

❯ _
```

## Slash Commands

| Command | Description |
|---------|-------------|
| **Analysis** | |
| `/qc` | Quality control (FastQC) |
| `/align` | Align reads to reference genome |
| `/variant-call` | Call variants (GATK/FreeBayes) |
| `/annotate` | Annotate variants (SnpEff/VEP) |
| `/pipeline` | Full pipeline: QC → align → call → annotate |
| **Comparative** | |
| `/blast` | BLAST similarity search |
| `/msa` | Multiple sequence alignment |
| `/phylo` | Phylogenetic tree construction |
| **Exploration** | |
| `/summary` | Summarize a genomic file |
| `/search` | Query databases (NCBI, Ensembl...) |
| `/explain` | Explain a variant, gene, or region |
| **Session** | |
| `/mcp` | Manage MCP servers (connect, status) |
| `/swarm` | Show background analyses |
| `/provider` | Switch AI provider |
| `/model` | Switch model |
| `/help` | Show available commands |

## Architecture

```
┌─────────────────────────────────────────────┐
│              genomix-cli                     │
│                                              │
│  CLI/TUI ── Agent Loop ── Swarm Manager      │
│                 │                             │
│    ┌────────────┼────────────┐                │
│    ▼            ▼            ▼                │
│  Tool       Skills       Project              │
│  Registry   System       Manager              │
│    │                                          │
│    ▼                                          │
│  MCP Servers                                  │
│  ├── biotools: samtools, BWA, GATK,           │
│  │   BLAST+, FastQC                           │
│  └── databases: NCBI, Ensembl,                │
│      ClinVar, dbSNP                           │
│                                               │
│  AI Providers                                 │
│  Ollama (local) │ Claude │ OpenAI             │
└───────────────────────────────────────────────┘
```

## Configuration

```yaml
# ~/.genomix/config.yaml
provider:
  default: opencode        # ollama local (default)
  model: qwen3-coder:30b

# Or use Claude/OpenAI:
# provider:
#   default: claude
#   model: claude-sonnet-4-6
```

API keys (if using cloud providers):
```yaml
# ~/.genomix/secrets.yaml (mode 0600)
anthropic_api_key: "sk-ant-..."
openai_api_key: "sk-..."
```

## Contributing

Contributions welcome! This project is in early alpha.

- **Spec:** `docs/superpowers/specs/2026-03-21-genomix-cli-design.md`
- **Plan:** `docs/superpowers/plans/2026-03-21-genomix-cli.md`
- **Skills guide:** Create custom skills in `.genomix/skills/` following the SKILL.md format

## License

Apache 2.0
