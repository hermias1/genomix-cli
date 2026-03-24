---
name: variant-prioritize
description: Filter and prioritize variants from large VCF files (exomes, genomes)
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [clinical, prioritization, filtering, exome]
    tools_used: [filter_vcf, read_file, gnomad_variant, clinvar_search]
---

# Variant Prioritization

For large VCF files (exomes with 30K+ variants, genomes with 4M+ variants), help the user filter down to clinically relevant variants.

## Strategy

1. **Ask the user** what they're looking for:
   - Disease area (cancer, cardiac, neurological, rare disease)?
   - Any specific gene panel?
   - Family history?

2. **Filter using filter_vcf tool**:
   - If gene panel specified: filter by gene list
   - If looking for rare variants: use exclude_common=true
   - If looking for protein-altering: filter types to SNV,deletion,insertion

3. **Common gene panels** (use your knowledge):
   - Hereditary cancer: BRCA1,BRCA2,TP53,PALB2,ATM,CHEK2,PTEN,CDH1,STK11,MLH1,MSH2,MSH6,PMS2,APC,MUTYH
   - Cardiac: MYBPC3,MYH7,TNNT2,TNNI3,LMNA,SCN5A,KCNQ1,KCNH2,RYR2,DSP,PKP2
   - Pharmacogenomics: CYP2D6,CYP2C19,CYP2C9,DPYD,VKORC1,TPMT,UGT1A1,SLCO1B1
   - ACMG-73 secondary findings: standard list of 73 medically actionable genes

4. **Present results** grouped by gene, with variant count and types

5. For the most interesting variants (pathogenic/likely pathogenic, or in critical genes), provide brief interpretation
