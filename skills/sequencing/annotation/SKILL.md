---
name: annotation
description: Annotate variants with SnpEff and VEP, interpret functional impact and clinical significance
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [sequencing, annotation, snpeff, vep, clinical, impact]
    tools_used: [run_command, read_file, ncbi_search]
---

# Variant Annotation with SnpEff and VEP

## Tool Selection

| Tool | Best For |
|------|----------|
| SnpEff | Fast functional annotation, research use, large cohorts |
| VEP (Ensembl) | Clinical use, richer plugin ecosystem (CADD, SpliceAI, dbNSFP) |

Use VEP for clinical interpretation. Use SnpEff for rapid exploratory analysis.

## SnpEff Annotation

```bash
snpEff ann \
  -v \
  -stats sample.snpEff.html \
  GRCh38.105 \
  sample.filtered.vcf.gz \
  | bgzip > sample.annotated.vcf.gz
```

Key ANN fields: `Allele | Effect | Impact | Gene | Feature | HGVSc | HGVSp`

Impact levels:
- **HIGH**: frameshift, stop_gained, splice_donor — likely loss of function.
- **MODERATE**: missense, in-frame indel — may affect protein function.
- **LOW**: synonymous, splice_region — usually benign.
- **MODIFIER**: intergenic, intronic — typically no direct effect.

## VEP Annotation

```bash
vep \
  --input_file sample.filtered.vcf.gz \
  --output_file sample.vep.vcf \
  --vcf \
  --cache \
  --assembly GRCh38 \
  --everything \
  --fork 4
```

`--everything` enables: sift, polyphen, ccds, hgvs, symbol, numbers, domains, regulatory, canonical, protein, biotype, uniprot, tsl, appris, variant_class.

## Clinical Impact Interpretation

After annotation, prioritize variants by:

1. **ClinVar significance**: pathogenic > likely_pathogenic > VUS > likely_benign > benign.
2. **ACMG criteria**: apply PVS1 (null variant in LoF gene), PS1/PS2 (same AA / de novo), PM1–PM6, PP1–PP5.
3. **Population frequency**: AF > 1% in gnomAD is strong evidence against pathogenicity for rare disease.
4. **Functional predictions**: CADD ≥ 20 (top 1% most deleterious), SIFT < 0.05 (damaging), PolyPhen > 0.85 (probably damaging).

Always cross-reference with OMIM for gene-disease relationships and check if the variant has been reported in ClinVar with supporting evidence (gold stars ≥ 1 preferred).

## Reporting Fields

Minimum fields for a clinical annotation report:
- Gene symbol, transcript ID, HGVSc, HGVSp
- Consequence (VEP) / Effect (SnpEff)
- ClinVar ID and clinical significance
- gnomAD AF (overall and population-specific)
- CADD Phred score
- Zygosity (from VCF GT field)
