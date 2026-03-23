---
name: clinical-report
description: Generate a structured clinical variant report with structural and pharmacogenomic context
version: 2.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [reporting, clinical, variants, structure, oncogenetics]
    tools_used: [read_file, clinvar_search, uniprot_gene_to_accession, alphafold_prediction]
---

# Clinical Variant Report Generation

When generating a clinical report from a VCF file:

1. **Read the VCF** and identify all variants
2. **For each variant**, determine:
   - Gene, variant type, zygosity, clinical significance
   - For missense variants: structural domain and AlphaFold confidence
3. **Respond with a JSON array** of variants:

```json
[
  {
    "gene": "BRCA1",
    "variant": "chr17:43094464 G>A",
    "type": "missense_variant",
    "zygosity": "Heterozygous",
    "significance": "Pathogenic",
    "domain": "BRCT domain (critical for DNA repair)",
    "structural_confidence": "High (pLDDT 91)"
  }
]
```

Include "domain" and "structural_confidence" fields when you know them from your
knowledge of well-characterized proteins. You don't need to query AlphaFold for
every variant — use your knowledge for major genes (BRCA1/2, TP53, EGFR, etc.).

IMPORTANT: Return ONLY the JSON array. Keep it concise. List ALL variants.
