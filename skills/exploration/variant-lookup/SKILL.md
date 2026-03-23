---
name: variant-lookup
description: Comprehensive variant lookup with structural context across ClinVar, gnomAD, Ensembl, AlphaFold
version: 2.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [exploration, variants, lookup, structure]
    tools_used: [clinvar_search, gnomad_variant, ensembl_variant_info, uniprot_gene_to_accession, alphafold_prediction, interpro_protein]
---

# Comprehensive Variant Lookup

When the user asks to look up a variant:

1. **Identify** the variant (rsID, coordinates, or HGVS notation)
2. **Clinical significance** — query ClinVar (clinvar_search)
3. **Population frequency** — query gnomAD or Ensembl for allele frequencies
4. **Structural context** (for missense variants):
   a. Resolve gene → UniProt ID (uniprot_gene_to_accession)
   b. Get AlphaFold structure confidence at the variant position (alphafold_prediction)
   c. Check if variant falls in a known protein domain (interpro_protein)
   d. Report: "This variant is in the [domain name], a region with [high/low] structural confidence (pLDDT [score])"
5. **Synthesize** a comprehensive report:
   - Clinical classification (pathogenic/VUS/benign)
   - Population frequencies (rare/common across ancestries)
   - Structural impact (domain, confidence, predicted effect)
   - Disease associations
   - Literature references if relevant

For missense variants, ALWAYS include structural context — it's critical for interpretation.
Use at most 4-5 database calls total. Prioritize: ClinVar → structural → frequency.
