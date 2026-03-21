---
name: variant-explain
description: Explain genetic variants in plain language, cite ClinVar and dbSNP evidence, and assess clinical significance
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [exploration, variants, clinvar, dbsnp, clinical, interpretation]
    tools_used: [ncbi_search, read_file]
---

# Explaining Variants in Plain Language

## Variant Notation

Understand the notation before explaining:

| Notation | Meaning |
|----------|---------|
| `c.185delAG` | Deletion of AG at coding position 185 (frameshift) |
| `p.Glu23ValfsTer17` | Glutamate at position 23 changed, frameshift, stop at +17 |
| `p.Val600Glu` (p.V600E) | Valine to glutamic acid at position 600 |
| `g.41245466G>A` | Genomic substitution G to A at chr17:41245466 |
| `rs28897696` | dbSNP reference SNP ID |

For a non-specialist audience, translate to: "A change in the BRCA1 gene where the letter G in the DNA is replaced by A."

## Plain Language Template

When explaining a variant, use this structure:

1. **What is it?** — Name the gene, type of change (substitution, deletion, insertion), and location.
2. **What does the gene do?** — One sentence on normal function.
3. **What does this change do?** — Effect on the protein (if any): stops it early, changes its shape, or has no effect.
4. **Is it known to cause disease?** — ClinVar classification and evidence level.
5. **How common is it?** — Population frequency from gnomAD.
6. **What should someone do with this information?** — Recommend genetic counseling for pathogenic/likely pathogenic variants; reassure for benign.

## ClinVar Evidence Levels

| Stars | Review Status | Weight |
|-------|---------------|--------|
| 4 | Practice guideline | Highest |
| 3 | Expert panel reviewed | High |
| 2 | Multiple submitters, no conflict | Medium |
| 1 | Single submitter | Lower |
| 0 | No assertion criteria | Lowest |

When citing ClinVar: "This variant (rs28897696) has been classified as **Pathogenic** by 12 submitters with no conflicts (2-star review status in ClinVar, accession RCV000031284)."

## dbSNP Citation

dbSNP stores population frequency data from 1000 Genomes, gnomAD, and TOPMed. When citing:
"According to dbSNP (rs80359550), this variant has an allele frequency of 0.0003 in the global gnomAD v3 population, confirming it is rare."

For variants with no rsID, note: "This variant is not currently in dbSNP and should be treated as a novel finding."

## Key Phrases for Non-Specialists

- Pathogenic → "This change is known to cause [disease] based on strong scientific evidence."
- Likely pathogenic → "This change is probably disease-causing, but more evidence is being gathered."
- VUS (Variant of Uncertain Significance) → "We cannot yet determine whether this change is harmful. It does not mean you have a disease."
- Likely benign / Benign → "This change is considered a normal variation with no health implications."

Always include a disclaimer: "This explanation is for informational purposes only. Please consult a certified genetic counselor or medical professional for clinical decisions."
