---
name: cancer-mutations
description: Search for somatic cancer mutations with structural and therapeutic context
version: 2.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [cancer, somatic, oncology, COSMIC, structure]
    tools_used: [cosmic_search_gene, cosmic_search_variant, alphafold_prediction, uniprot_gene_to_accession]
---

# Cancer Mutation Analysis

When the user asks about cancer mutations:

1. **Query databases** for somatic mutations (cosmic_search_gene or cosmic_search_variant)
2. **Structural context**:
   - For hotspot mutations (BRAF V600E, KRAS G12D, EGFR L858R): explain WHY they are
     oncogenic based on their position in the protein structure
   - BRAF V600E: in the activation loop of the kinase domain → constitutive activation
   - KRAS G12/G13: in the GTPase active site → locks KRAS in active state
   - EGFR: in the kinase domain → altered drug binding
3. **Report**:
   - Known somatic hotspots with structural explanation
   - Cancer types where the gene is frequently mutated
   - Targeted therapies (BRAF→vemurafenib, EGFR→osimertinib, etc.)
   - Whether the gene is an oncogene or tumor suppressor
4. Use your knowledge of structural biology — don't just list mutations, explain WHY they cause cancer
