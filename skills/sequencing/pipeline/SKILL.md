---
name: pipeline
description: Run the full NGS analysis pipeline (QC → align → variant-call → annotate)
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [sequencing, pipeline, workflow]
    tools_used: [read_file, fastqc_analyze, bwa_mem, samtools_sort, samtools_index, gatk_haplotype_caller]
---

# Full Analysis Pipeline

When the user runs /pipeline with input file(s):

1. **QC** — Run FastQC on the input FASTQ files. Report quality summary.
2. **Alignment** — Align reads to the reference genome using BWA-MEM.
3. **Sort & Index** — Sort the BAM and create index with samtools.
4. **Variant Calling** — Call variants with GATK HaplotypeCaller.
5. **Summary** — Report number of reads, alignment rate, and variants found.

Report each step's status as you go. If a tool is not available (missing binary),
skip it and note what would have been done.

This is a sequential workflow — each step depends on the previous one.
