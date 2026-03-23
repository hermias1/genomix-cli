---
name: disease-association
description: Find diseases associated with a gene using OMIM
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [diseases, OMIM, gene-phenotype]
    tools_used: [omim_gene_disease, omim_search]
---

# Gene-Disease Association

When the user asks about diseases for a gene:

1. **Query OMIM** using omim_gene_disease for the gene symbol
2. **Supplement** with your knowledge of well-known gene-disease relationships
3. **Report**:
   - Associated diseases/phenotypes with MIM numbers
   - Inheritance pattern (AD, AR, XL, etc.)
   - Key clinical features
   - Whether the gene is actionable (ACMG secondary findings list)
4. Keep responses focused and clinically relevant
