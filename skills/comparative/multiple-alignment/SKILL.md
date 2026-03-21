---
name: multiple-alignment
description: Perform multiple sequence alignment with MAFFT, choose the right algorithm, and interpret output
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [comparative, mafft, multiple-alignment, msa, phylogenetics]
    tools_used: [run_command, read_file]
---

# Multiple Sequence Alignment with MAFFT

## When to Use MAFFT

Use multiple sequence alignment (MSA) when you need to:
- Compare homologous sequences to identify conserved regions.
- Prepare input for phylogenetic tree construction.
- Detect insertions/deletions (indels) across taxa.
- Find functional motifs conserved across species.

MAFFT is preferred over Clustal Omega for most tasks: it scales to thousands of sequences and handles both protein and nucleotide input.

## Algorithm Selection

| Flag | Algorithm | Use When |
|------|-----------|----------|
| `--auto` | Auto-select | Default; let MAFFT decide based on input size |
| `--localpair --maxiterate 1000` (L-INS-i) | Iterative local alignment | <200 sequences, highly accurate, long gaps expected |
| `--globalpair --maxiterate 1000` (G-INS-i) | Iterative global alignment | <200 sequences, global homology throughout |
| `--ep 0 --genafpair --maxiterate 1000` (E-INS-i) | Iterative with multiple conserved domains | <200 sequences, unalignable regions between conserved blocks |
| `--retree 2 --maxiterate 0` (FFT-NS-2) | Progressive | >1000 sequences, speed is priority |

For phylogenetics: use L-INS-i or G-INS-i on <200 sequences for best accuracy.

## Basic Commands

```bash
# Protein alignment (auto mode)
mafft --auto --thread 4 input.fasta > aligned.fasta

# High-accuracy nucleotide alignment (<200 seqs)
mafft --localpair --maxiterate 1000 --thread 4 input.fasta > aligned.fasta

# Large dataset (>500 seqs)
mafft --retree 2 --maxiterate 0 --thread 8 input.fasta > aligned.fasta
```

## Output Interpretation

MAFFT outputs FASTA with gaps represented as `-`. All sequences are padded to the same length.

Key things to check:
- **Alignment length vs. average sequence length**: A ratio > 3x suggests many large insertions or misaligned sequences — consider removing outliers.
- **Conserved columns**: Columns with identical residues across all sequences indicate functional/structural constraints.
- **Gap-rich regions**: Highly gapped columns (>50% gaps) are often unreliable — mask them before phylogenetic analysis using trimAl or Gblocks.

## Downstream Processing

Before building a phylogenetic tree, trim poorly aligned columns:

```bash
trimal -in aligned.fasta -out trimmed.fasta -automated1
```

Visualize alignments with AliView or JalView to inspect quality before proceeding.
