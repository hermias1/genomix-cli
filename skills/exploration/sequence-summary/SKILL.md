---
name: sequence-summary
description: Auto-detect sequence file format and report key statistics including length, GC content, and quality
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [exploration, fasta, fastq, statistics, gc-content, summary]
    tools_used: [read_file, run_command]
---

# Sequence File Summary

## Auto-Detecting File Format

Inspect the first few bytes of the file:

| First character | Format |
|-----------------|--------|
| `>` | FASTA |
| `@` | FASTQ |
| `BAM\1` (binary) | BAM |
| `##fileformat=VCF` | VCF |
| `##gff-version` | GFF |

For compressed files (`.gz`), decompress the header only:

```bash
zcat file.fastq.gz | head -4
```

If the file extension contradicts the content, trust the content and flag the mismatch.

## FASTA Summary Statistics

Key metrics to report:
- **Total sequences**: count of `>` header lines.
- **Total bases**: sum of all sequence character lengths (exclude gaps for aligned FASTA).
- **Min / Max / Mean / N50 length**: for assemblies, N50 is the primary metric (length such that 50% of bases are in sequences of this length or longer).
- **GC content (%)**: (G + C) / (A + T + G + C) × 100. Exclude ambiguous bases (N).
- **N content (%)**: proportion of unknown bases.

```bash
seqkit stats -a sequences.fasta
```

For assemblies, also report L50, N90, and number of sequences >1 kb.

## FASTQ Summary Statistics

Key metrics:
- **Total reads**: number of `@` header lines.
- **Total bases**: sum of sequence lengths.
- **Mean read length** and **length distribution**.
- **Mean quality score** (Q-score per read, then overall mean).
- **% Q20 bases / % Q30 bases**: fraction of bases above quality thresholds.
- **% GC**: mean GC content across all reads.

```bash
seqkit stats -a sample.fastq.gz
# or
fastqc --nogroup sample.fastq.gz
```

## GC Content Interpretation

Expected GC% ranges by organism:
- Human: ~41%
- Mouse: ~42%
- E. coli: ~51%
- Plasmodium falciparum: ~19%
- Streptomyces: ~70–73%

GC outside the expected range by >5% may indicate:
- Wrong organism (contamination).
- Biased library preparation (GC-rich adapter ligation).
- Low-complexity or repetitive regions dominating the file.

## Report Format

When summarizing a file, output:
```
File: <filename>
Format: <FASTA/FASTQ>
Sequences/Reads: <N>
Total bases: <N bp>
GC content: <X.X%>
Mean length: <N bp>
Min/Max length: <N>/<N> bp
[FASTQ only] % Q30: <X.X%>
[Assembly only] N50: <N bp>
```
