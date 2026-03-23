---
name: protein-domains
description: Look up protein domain annotations from InterPro
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [protein, domains, structure, InterPro]
    tools_used: [interpro_protein, interpro_search]
---

# Protein Domain Lookup

When the user asks about protein domains:

1. **Query InterPro** using interpro_protein (by UniProt ID) or interpro_search (by keyword)
2. **Report**:
   - Protein family classification
   - Functional domains (with positions)
   - Active sites and binding sites
   - Conservation and evolutionary context
3. If the user provides a gene name, use your knowledge to find the UniProt ID
4. Explain how variant location relative to domains affects function
