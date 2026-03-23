---
name: cancer-mutations
description: Search for somatic cancer mutations and cancer gene associations
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [cancer, somatic, oncology, COSMIC]
    tools_used: [cosmic_search_gene, cosmic_search_variant, cosmic_cancer_genes]
---

# Cancer Mutation Lookup

When the user asks about cancer mutations:

1. **Query COSMIC** using cosmic_search_gene or cosmic_search_variant
2. **Report**:
   - Known somatic mutations in the gene
   - Cancer types where the gene is frequently mutated
   - Hotspot mutations (e.g., BRAF V600E, KRAS G12D)
   - Whether the gene is a known oncogene or tumor suppressor
3. Use your knowledge of major cancer genes (TP53, KRAS, BRAF, EGFR, PIK3CA, etc.)
4. Mention relevant targeted therapies if applicable
