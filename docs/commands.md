# Genomix CLI — Command Reference

Complete reference for all 20 slash commands available in genomix.

---

## Analysis

### `/qc`
Run quality control on sequencing data (FastQC).

```
/qc data/reads.fastq.gz
```

Analyzes read quality, adapter contamination, GC content, and provides trimming recommendations. Requires FastQC installed (`brew install fastqc`).

### `/align`
Align reads to a reference genome (BWA-MEM2).

```
/align data/sample_R1.fastq.gz
```

Detects paired-end reads, checks reference index, runs alignment. Output: sorted BAM in `data/processed/`. Requires BWA installed (`brew install bwa`).

### `/variant-call`
Call germline variants (GATK HaplotypeCaller).

```
/variant-call data/processed/sample.sorted.bam
```

Follows GATK best practices: MarkDuplicates → BaseRecalibrator → HaplotypeCaller. Output: VCF in `data/processed/`. Requires GATK installed.

### `/annotate`
Annotate variants with functional impact (SnpEff/VEP).

```
/annotate data/processed/sample.vcf.gz
```

Adds gene names, variant effects, clinical significance. Output: annotated VCF.

### `/pipeline`
Run the full pipeline: QC → align → variant-call → annotate.

```
/pipeline data/sample_R1.fastq.gz
```

Chains all analysis steps automatically. Saves outputs in `data/processed/` and `reports/`.

---

## Comparative Genomics

### `/blast`
BLAST similarity search against a database.

```
/blast query.fasta
/blast data/unknown_sequence.fasta
```

Auto-selects the right BLAST program (blastn, blastp, blastx) based on sequence type. Interprets e-values and alignments. Requires BLAST+ installed (`brew install blast`).

### `/msa`
Multiple sequence alignment (MAFFT).

```
/msa sequences.fasta
```

Aligns multiple sequences, chooses the right MAFFT algorithm based on dataset size. Output: aligned FASTA.

### `/phylo`
Build a phylogenetic tree (FastTree).

```
/phylo aligned_sequences.fasta
```

Constructs a tree from an alignment, outputs Newick format. Interprets bootstrap support values.

---

## Exploration

### `/summary`
Summarize any genomic file.

```
/summary data/sample.vcf
/summary data/reads.fastq.gz
/summary data/genome.fasta
```

Auto-detects file format (FASTA, FASTQ, VCF, BAM, GFF) and reports key statistics: sequence count, length distribution, variant count, quality scores, etc.

### `/search`
Search genomic databases (NCBI, Ensembl, ClinVar...).

```
/search BRCA1 breast cancer
/search cystic fibrosis CFTR
```

Designs effective search strategies across multiple databases and combines results.

### `/explain`
Explain a variant, gene, or genomic region in plain language.

```
/explain rs7412
/explain BRCA1
/explain chr17:43094464 G>A
```

Provides clinical significance, population frequency, structural context, and disease associations. Adapts language to user expertise (biologist vs specialist).

### `/lookup`
Comprehensive variant lookup across all databases.

```
/lookup rs334
/lookup chr17:7668202
```

Queries ClinVar, gnomAD, Ensembl, and checks structural context (protein domain, AlphaFold confidence). The most thorough single-variant analysis.

---

## Clinical

### `/report`
Generate a styled HTML clinical report from a VCF file.

```
/report patient.vcf
/report patient.vcf --output reports/custom_name.html
```

Reads the VCF, identifies all variants, generates an HTML report with:
- Variant summary table with ACMG significance badges
- Clinical interpretation
- Recommendations (genetic counseling, surveillance, carrier testing)
- Open with: `open reports/patient_report.html`

### `/drug`
Look up drug-gene interactions (PharmGKB).

```
/drug CYP2D6
/drug warfarin
/drug tamoxifen
```

Returns pharmacogenomic annotations, dosing guidelines, and clinical actionability for drug-gene pairs.

### `/disease`
Find diseases associated with a gene (OMIM).

```
/disease BRCA1
/disease CFTR
/disease TP53
```

Returns OMIM disease entries, inheritance patterns, and key clinical features.

### `/frequency`
Look up population allele frequencies (gnomAD).

```
/frequency rs334
/frequency 7-117559593-ATCT-A
```

Returns allele frequencies across populations (AFR, EUR, EAS, SAS, AMR). Interprets rarity and implications for variant classification (ACMG BA1/BS1).

---

## Oncology

### `/cancer`
Search for somatic cancer mutations (COSMIC).

```
/cancer BRAF V600E
/cancer TP53
/cancer KRAS
```

Returns known hotspot mutations with structural explanation (why they're oncogenic), cancer types, and targeted therapies.

---

## Literature

### `/literature`
Search scientific literature (PubMed).

```
/literature BRCA1 breast cancer risk
/literature rs334 sickle cell
/literature CRISPR gene therapy
```

Returns top relevant articles with titles, authors, journal, and PubMed IDs. Can fetch abstracts on request.

---

## Structural Biology

### `/domains`
Look up protein domain annotations (InterPro).

```
/domains BRCA1
/domains P04637
```

Returns protein families, functional domains with positions, active sites, and conservation context.

### `/structure`
Protein structure analysis (AlphaFold + PDB).

```
/structure TP53
/structure BRCA1
/structure EGFR
```

Resolves gene → UniProt → AlphaFold prediction + experimental PDB structures. Reports:
- AlphaFold confidence (pLDDT scores)
- Disordered vs structured regions
- Available experimental structures
- Functional domains
- Where pathogenic variants cluster

---

## Session Management

### `/mcp`
Manage MCP (Model Context Protocol) servers.

```
/mcp                    # Show all servers and status
/mcp connect            # Connect all available servers
/mcp connect ncbi       # Connect a specific server
/mcp disconnect ncbi    # Disconnect a server
```

Shows a table of all 18 MCP servers with connection status, tool count, and descriptions.

### `/provider`
Switch AI provider interactively.

```
/provider               # Interactive selector (recommended)
/provider claude        # Quick switch to Claude
/provider ollama        # Quick switch to Ollama
/provider openai        # Quick switch to OpenAI
```

The interactive selector shows all options, handles API key setup, and model selection in one flow.

### `/model`
Switch AI model.

```
/model                      # Interactive model selector
/model claude-opus-4-6      # Quick switch
/model qwen3.5              # Switch Ollama model
```

### `/swarm`
Show background analyses.

```
/swarm                  # List all background tasks
```

Displays task ID, command, and status (running/completed/failed).

### `/history`
Browse session history.

```
/history                # List recent sessions
/history BRCA1          # Search sessions mentioning BRCA1
```

Sessions are stored in SQLite with full-text search.

### `/help`
Show all available commands grouped by category.

### `/quit`
Exit genomix (also: `/exit`, `/q`, or Ctrl+D).

---

## Non-Interactive Mode

All commands can also be used non-interactively:

```bash
# Ask a question
genomix ask "What is the BRCA1 gene?"

# Run a slash command
genomix run /qc data/reads.fastq.gz
genomix run /summary data/sample.vcf

# Pipe input
echo "Explain rs7412" | genomix ask

# JSON output
genomix run /qc data/reads.fastq.gz --format json
```
