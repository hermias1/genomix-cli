---
name: drug-interaction
description: Look up pharmacogenomic drug-gene interactions and dosing guidelines
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [pharmacogenomics, drugs, clinical]
    tools_used: [pharmgkb_gene, pharmgkb_drug, pharmgkb_variant]
---

# Drug-Gene Interaction Lookup

When the user asks about drug interactions for a gene or variant:

1. **Query PharmGKB** for the gene or drug using pharmgkb_gene or pharmgkb_drug
2. **Identify** clinically actionable drug-gene pairs (e.g., CYP2D6-tamoxifen, VKORC1-warfarin)
3. **Report**:
   - Which drugs are affected by variants in this gene
   - Dosing recommendations (if available)
   - Level of evidence (1A, 1B, 2A, etc.)
   - Actionable clinical guidelines
4. Use your knowledge of common pharmacogenes (CYP2D6, CYP2C19, VKORC1, DPYD, TPMT, UGT1A1)
