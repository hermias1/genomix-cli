---
name: file-formats
description: Recognize and validate FASTA, FASTQ, BAM, VCF, and GFF files by inspecting their content
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [common, file-formats, fasta, fastq, bam, vcf, gff, detection]
    tools_used: [read_file, run_command]
---

# Genomic File Format Recognition

## Detection by Content

Never rely solely on file extensions — always verify content.

### FASTA
- First non-empty line starts with `>`.
- Second line is a sequence (A, T, G, C, N, IUPAC ambiguity codes, or amino acid letters).
- Multi-line sequences are allowed; next record starts with `>`.

```
>sequence_id optional description
ATCGATCGATCG
ATCGATCGATCG
```

### FASTQ
- Records are 4 lines: `@header`, sequence, `+` (optionally repeated header), quality string.
- Quality string length must equal sequence length.
- Quality characters are ASCII 33–126 (Phred+33 encoding for modern Illumina).

```
@read_id
ATCGATCGATCG
+
FFFFIIIIBBBB
```

Distinguish FASTQ from FASTA: FASTQ starts with `@`, FASTA with `>`. Note: `@` also appears in quality lines, so always check that records are 4 lines.

### BAM / SAM
- **SAM**: plain text; starts with `@HD` (header line), `@SQ` (reference sequences), then alignment records (11 mandatory tab-separated fields).
- **BAM**: binary; magic bytes are `BAM\1` (hex `42 41 4D 01`). Use `samtools view -H` to inspect.

```bash
samtools view -H sample.bam | head -5
```

### VCF
- Starts with `##fileformat=VCFv4.x`.
- Meta-information lines begin with `##`.
- Header line begins with `#CHROM`.
- Data lines: CHROM, POS, ID, REF, ALT, QUAL, FILTER, INFO (+ optional FORMAT and sample columns).

```
##fileformat=VCFv4.2
#CHROM  POS     ID          REF  ALT  QUAL  FILTER  INFO
chr17   41245466 rs28897696  G    A    100   PASS    .
```

### GFF / GTF
- GFF3: starts with `##gff-version 3`. 9 tab-separated fields; attributes in `key=value` format.
- GTF (GFF2): attributes in `key "value"` format (used by GENCODE, Ensembl downloads).

```
##gff-version 3
chr1  RefSeq  gene  11874  14409  .  +  .  ID=gene1;Name=DDX11L1
```

## Format Validation Commands

```bash
# Check FASTA integrity
seqkit stats sequences.fasta

# Validate FASTQ (check pairing, quality encoding)
fastqc --nogroup sample.fastq.gz

# Validate BAM (check for truncation, index)
samtools quickcheck sample.bam && samtools index sample.bam

# Check VCF (validate against spec)
bcftools stats sample.vcf.gz | head -30
```

## Common Pitfalls

- **FASTA with wrapped lines**: parsers must handle variable line widths.
- **FASTQ quality encoding**: older data may use Phred+64 (Illumina 1.3–1.7); seqkit or FastQC can auto-detect.
- **Multi-sample VCF**: sample columns appear after FORMAT — always check the header for sample names.
- **BGZF vs gzip**: BAM and indexed VCF use BGZF (block gzip), which is compatible with regular gzip but supports random access via `.tbi` / `.csi` indexes.
