---
name: variant-calling
description: Call germline variants following GATK best practices, from BAM to filtered VCF
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [sequencing, variant-calling, gatk, germline, vcf]
    tools_used: [run_command, read_file]
---

# Germline Variant Calling with GATK Best Practices

## Pipeline Overview

1. Mark duplicates (MarkDuplicates)
2. Base Quality Score Recalibration (BQSR)
3. HaplotypeCaller → GVCF
4. GenomicsDBImport (for cohorts) or direct genotyping
5. GenotypeGVCFs → raw VCF
6. Variant Quality Score Recalibration (VQSR) or hard filtering

## Step 1: Mark Duplicates

```bash
gatk MarkDuplicates \
  -I sample.sorted.bam \
  -O sample.markdup.bam \
  -M sample.markdup.metrics \
  --CREATE_INDEX true
```

Duplication rate >30% in WGS warrants investigation. Amplicon data will have high duplication by design — use `--REMOVE_DUPLICATES false` and note in report.

## Step 2: Base Quality Score Recalibration

Requires a known-sites VCF (dbSNP, Mills indels for human):

```bash
gatk BaseRecalibrator \
  -I sample.markdup.bam \
  -R reference.fa \
  --known-sites dbsnp_146.hg38.vcf.gz \
  --known-sites Mills_and_1000G_gold_standard.indels.hg38.vcf.gz \
  -O sample.recal.table

gatk ApplyBQSR \
  -I sample.markdup.bam \
  -R reference.fa \
  --bqsr-recal-file sample.recal.table \
  -O sample.recal.bam
```

## Step 3: HaplotypeCaller (GVCF mode)

```bash
gatk HaplotypeCaller \
  -R reference.fa \
  -I sample.recal.bam \
  -O sample.g.vcf.gz \
  -ERC GVCF \
  --dbsnp dbsnp_146.hg38.vcf.gz
```

For targeted sequencing, add `-L intervals.bed` to restrict calling to the panel regions.

## Step 4: Genotyping

Single sample:
```bash
gatk GenotypeGVCFs \
  -R reference.fa \
  -V sample.g.vcf.gz \
  -O sample.raw.vcf.gz
```

## Step 5: Hard Filtering (small cohorts / no VQSR)

SNPs:
```bash
gatk VariantFiltration \
  -V sample.raw.vcf.gz \
  --select-type-to-include SNP \
  --filter-expression "QD < 2.0" --filter-name "QD2" \
  --filter-expression "FS > 60.0" --filter-name "FS60" \
  --filter-expression "MQ < 40.0" --filter-name "MQ40" \
  -O sample.snp.filtered.vcf.gz
```

Indels: use `QD < 2.0`, `FS > 200.0`, `ReadPosRankSum < -20.0`.

Variants passing all filters will have FILTER=PASS in the output VCF.
