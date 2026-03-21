# 🧬 Genomix CLI

AI-powered command-line tool for DNA sequence and genome analysis.

Genomix CLI is an intelligent orchestrator that uses AI to help you analyze genomic data. Ask questions in natural language or use slash commands — the AI selects and runs the right bioinformatics tools, queries databases, and explains results.

## Features

- **Natural language interface** — ask questions about your genomic data
- **Slash commands** — `/qc`, `/align`, `/variant-call`, `/annotate`, `/blast`, `/msa`, `/phylo`, and more
- **9 MCP servers** — wrapping samtools, BWA, GATK, BLAST+, FastQC, NCBI, Ensembl, ClinVar, dbSNP
- **12 built-in skills** — specialized AI instructions for genomics workflows
- **3 AI providers** — Claude (default), OpenAI, or local via Ollama
- **Privacy mode** — run with local models for sensitive/patient data
- **Background analyses** — long-running tasks via the swarm manager

## Installation

```bash
pip install genomix-cli
genomix setup
```

## Quick Start

```bash
# Initialize a project
genomix init

# Start interactive mode
genomix

# Non-interactive usage
genomix run /qc data/reads.fastq.gz
genomix ask "What variants are in sample1.vcf?"
echo "Explain rs7412" | genomix ask
```

## Slash Commands

| Command | Description |
|---------|-------------|
| `/qc` | Quality control (FastQC) |
| `/align` | Align reads to reference |
| `/variant-call` | Call variants (GATK) |
| `/annotate` | Annotate variants |
| `/pipeline` | Full pipeline: QC → align → call → annotate |
| `/blast` | BLAST similarity search |
| `/msa` | Multiple sequence alignment |
| `/phylo` | Phylogenetic tree |
| `/summary` | Summarize a file |
| `/search` | Query databases |
| `/explain` | Explain a variant/gene |

## Architecture

```
CLI/TUI → Agent Loop → Tool Registry → MCP Servers (biotools + databases)
                ↓              ↓
          AI Provider    Skills System
    (Claude/OpenAI/Ollama)
```

## Contributing

Contributions welcome! See the spec at `docs/superpowers/specs/2026-03-21-genomix-cli-design.md`.

## License

Apache 2.0
