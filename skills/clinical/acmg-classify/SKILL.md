---
name: acmg-classify
description: Classify variants according to ACMG/AMP 2015 guidelines using evidence from multiple databases
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [clinical, ACMG, classification, variants]
    tools_used: [read_file, gnomad_variant, clinvar_search, alphafold_prediction, interpro_protein, ensembl_variant_info, uniprot_gene_to_accession]
---

# ACMG/AMP Variant Classification

Classify variants using the 2015 ACMG/AMP guidelines. For each variant, systematically evaluate evidence criteria:

## Evidence Criteria to Check

### Very Strong Pathogenic (PVS1)
- Null variant (nonsense, frameshift, canonical splice site, initiation codon) in a gene where loss-of-function is a known mechanism of disease
- Check: variant type from VCF, gene from [GENE:] tag

### Strong Pathogenic
- **PS1**: Same amino acid change as an established pathogenic variant → check ClinVar
- **PS3**: Well-established functional studies show damaging effect → check PubMed (use sparingly)

### Moderate Pathogenic
- **PM1**: Located in a mutational hotspot or well-established functional domain → check InterPro domains
- **PM2**: Absent from controls or extremely rare in gnomAD (AF < 0.0001) → check gnomAD
- **PM5**: Novel missense at a position where a different pathogenic missense exists → check ClinVar

### Supporting Pathogenic
- **PP3**: Computational evidence supports deleterious effect → AlphaMissense score > 0.564
- **PP5**: Reputable source reports variant as pathogenic → ClinVar with review stars ≥ 2

### Strong Benign
- **BA1**: Allele frequency > 5% in gnomAD → definitely benign
- **BS1**: Allele frequency greater than expected for disorder → gnomAD AF > 0.01

### Supporting Benign
- **BP4**: Computational evidence supports no impact → AlphaMissense score < 0.340
- **BP6**: Reputable source reports variant as benign → ClinVar

## Classification Rules
- **Pathogenic**: PVS1 + ≥1 Strong, or PVS1 + ≥2 Moderate, or ≥2 Strong, or 1 Strong + ≥3 Supporting
- **Likely Pathogenic**: PVS1 + 1 Moderate, or 1 Strong + 1-2 Moderate, or 1 Strong + ≥2 Supporting
- **Likely Benign**: 1 Strong Benign + 1 Supporting Benign, or ≥2 Supporting Benign
- **Benign**: BA1 alone, or ≥2 Strong Benign
- **VUS**: Doesn't meet above criteria, or conflicting evidence

## Output Format
For each variant, report:
1. Gene and variant description
2. Each evidence criterion evaluated (Met/Not Met/Not Applicable)
3. Final classification with reasoning
4. Confidence level

## Tool Strategy
- Read VCF (1 call) → get variants with [GENE:] tags
- gnomAD frequency for rare variants (1 call per variant, max 3)
- ClinVar check (1 call for batch)
- AlphaFold/InterPro only for missense variants (1-2 calls)
- Maximum 6-8 tool calls total. Use your knowledge for well-characterized genes.
