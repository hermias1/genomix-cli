# Changelog

## v0.4.2 — Hardening & Cleanup (2026-03-23)

### Added
- Live smoke tests for NCBI and Ensembl, opt-in via `GENOMIX_RUN_LIVE_SMOKE=1`
- Regression tests for privacy mode detection, bounded file previews, and structured report parsing

### Changed
- Unified slash command definitions across CLI and TUI via a shared command registry
- Hardened `/report` parsing and HTML sanitization for safer structured report generation
- Bounded `read_file` previews to avoid loading large genomics files fully into memory
- Fixed privacy mode detection for remote Ollama endpoints in non-interactive CLI flows

### Removed
- Dead `mcp_bridge` implementation and its unused unit tests

## v0.4.0 — Structural Biology Integration (2026-03-23)

### Added
- AlphaMissense pathogenicity predictions via `alphafold_missense` tool
- Structural context automatically included in variant analysis
- pLDDT confidence scores for variant position interpretation
- Expanded gene coordinate map (13 genes: TP53, EGFR, BRAF, KRAS, MLH1, PTEN, NRAS, MSH2, BRCA1, BRCA2, CFTR, HBB, APOE)

### Changed
- 5 skills upgraded to v2.0.0 with structural biology context
- Fixed double rendering bug in StreamingRenderer
- Fixed gene misidentification for same-chromosome genes

## v0.3.0 — Databases & Clinical Reports (2026-03-23)

### Added
- 9 new database MCP servers: gnomAD, OMIM, PharmGKB, COSMIC, InterPro, PubMed, AlphaFold, UniProt, PDB
- 8 new slash commands: /lookup, /drug, /disease, /literature, /frequency, /cancer, /domains, /structure
- `/report` command generates styled HTML clinical reports from VCF files
- CONTRIBUTING.md, docs/architecture.md, GitHub issue/PR templates
- All 5 biotools installed (samtools, bwa, gatk, blast, fastqc)

## v0.2.0 — Streaming Responses (2026-03-22)

### Added
- Real-time token-by-token streaming for all 3 providers
- StreamEvent typed system (TextDelta, ToolCallStart, ToolCallComplete, ToolResult)
- StreamingRenderer with Rich Live for paragraph-by-paragraph markdown
- Thinking spinner before first token
- Agent loop streaming with tool call accumulation

### Changed
- Refactored `chat()` to use `chat_stream()` internally

## v0.1.0 — Initial Release (2026-03-21)

### Added
- Interactive TUI with ASCII banner and slash command autocompletion
- 9 MCP servers (samtools, BWA, GATK, BLAST+, FastQC, NCBI, Ensembl, ClinVar, dbSNP)
- 12 built-in genomics skills
- 3 AI providers: Ollama (default), Claude, OpenAI
- Privacy mode for sensitive data
- Context compression for long conversations
- Session history with SQLite FTS5
- Non-interactive mode (genomix ask, genomix run)
- 81 tests
