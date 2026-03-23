---
name: variant-lookup
description: Comprehensive variant lookup across ClinVar, gnomAD, dbSNP, and Ensembl
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [exploration, variants, lookup]
    tools_used: [clinvar_search, gnomad_variant, dbsnp_search, ensembl_variant_info]
---

# Variant Lookup

When the user asks to look up a variant (rsID, coordinates, or HGVS notation):

1. **Identify** the variant format (rsID like rs334, coordinates like chr11:5226773, or HGVS)
2. **Query ClinVar** for clinical significance using clinvar_search
3. **Query gnomAD** for population frequencies using gnomad_variant (convert to chrom-pos-ref-alt format)
4. **Query Ensembl** for functional annotation using ensembl_variant_info
5. **Synthesize** a comprehensive summary:
   - Clinical significance (pathogenic/benign/VUS)
   - Population frequencies across ancestries (AFR, EUR, EAS, SAS)
   - Functional impact (gene, consequence, protein change)
   - Known disease associations
6. Present results in a clear, structured format

Use at most 3-4 database calls. Combine with your own knowledge for well-known variants.
