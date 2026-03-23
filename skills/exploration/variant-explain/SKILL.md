---
name: variant-explain
description: Explain genetic variants in plain language with structural and clinical context
version: 2.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [exploration, education, variants, structure]
    tools_used: [clinvar_search, ensembl_variant_info, uniprot_gene_to_accession, alphafold_prediction]
---

# Variant Explanation

When the user asks about a specific variant:

1. **Identify** the variant — rsID, coordinates, gene, transcript
2. **Locate** — chromosome, position, gene, protein change
3. **Impact** — coding effect (missense, nonsense, frameshift...)
4. **Clinical** — ClinVar significance, ACMG classification
5. **Structural context** (for missense/in-frame variants):
   - Where is this in the protein's 3D structure?
   - Is the affected residue in a functional domain?
   - What is the AlphaFold confidence at this position?
   - Would this change likely disrupt protein folding or function?
6. **Population** — allele frequency across populations
7. **Explain** in plain language adapted to the user's level:
   - For biologists: use HGVS nomenclature, cite sources, include structural reasoning
   - For non-specialists: analogies, avoid jargon, explain what it means for health

Example structural explanation:
"This variant changes amino acid 1685 from arginine to threonine in BRCA1.
It falls within the BRCT domain (positions 1646-1859), which is critical for
DNA damage repair. AlphaFold predicts this region with high confidence (pLDDT 91),
meaning the protein structure here is well-defined. Disrupting this domain
likely impairs BRCA1's tumor suppressor function."

Always cite sources (ClinVar ID, dbSNP rsID, PubMed).
