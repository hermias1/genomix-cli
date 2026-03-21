---
name: alignment
description: Align sequencing reads with BWA-MEM2, handle paired-end detection, and verify reference indexes
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [sequencing, alignment, bwa-mem2, paired-end, index]
    tools_used: [run_command, read_file]
---

# Read Alignment with BWA-MEM2

## When to Use BWA-MEM2

BWA-MEM2 is the successor to BWA-MEM with ~2x speedup via SIMD optimizations. Use it for:
- Short reads (70–300 bp) from Illumina sequencers against any reference ≤4 Gbp.
- Both whole-genome and targeted (exome, panel) sequencing.
- Paired-end and single-end reads.

For long reads (PacBio, Oxford Nanopore), use minimap2 instead.

## Reference Index Checking

Before aligning, confirm the index exists and is current:

```bash
# Index files expected: .0123, .amb, .ann, .bwt.2bit.64, .pac
ls -lh reference.fa.*
```

If any index file is missing or older than the reference FASTA, rebuild:

```bash
bwa-mem2 index reference.fa
```

Indexing a human genome (GRCh38, ~3 Gbp) takes ~1 hour and requires ~28 GB RAM.

## Paired-End Detection

Detect paired-end input by:
1. Checking for two input files (R1/R2 naming convention: `_R1_001.fastq.gz` / `_R2_001.fastq.gz`).
2. Inspecting read names in the FASTQ header — `/1` and `/2` suffixes, or Illumina space-delimited format: `@readname 1:N:0:ATCG`.
3. Counting reads in both files: they must be equal.

```bash
zcat sample_R1.fastq.gz | awk 'NR%4==1' | wc -l
zcat sample_R2.fastq.gz | awk 'NR%4==1' | wc -l
```

If counts differ, the file is truncated or mismatched — abort and report.

## Alignment Command

```bash
bwa-mem2 mem \
  -t 16 \
  -R "@RG\tID:sample1\tSM:sample1\tPL:ILLUMINA\tLB:lib1\tPU:unit1" \
  reference.fa \
  sample_R1_trimmed.fastq.gz \
  sample_R2_trimmed.fastq.gz \
  | samtools sort -@ 8 -o sample.sorted.bam

samtools index sample.sorted.bam
```

The `-R` read group tag is required downstream for GATK. Always include SM (sample name).

## Post-Alignment QC

Check alignment statistics:

```bash
samtools flagstat sample.sorted.bam
samtools idxstats sample.sorted.bam
```

Flag if:
- Mapped reads < 90% for WGS (contamination or wrong reference).
- Properly paired < 85% (insert size issues or truncated reads).
- Run `samtools stats` and plot with `plot-bamstats` for full diagnostics.
