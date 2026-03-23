---
name: protein-structure
description: Look up protein structure predictions (AlphaFold) and experimental structures (PDB)
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [protein, structure, AlphaFold, PDB]
    tools_used: [uniprot_gene_to_accession, alphafold_prediction, pdb_search_gene]
---

# Protein Structure Lookup

When the user asks about protein structure for a gene:

1. **Resolve gene to UniProt ID** using uniprot_gene_to_accession
2. **Get AlphaFold prediction** using alphafold_prediction with the UniProt ID
3. **Search PDB** for experimental structures using pdb_search_gene
4. **Report**:
   - AlphaFold confidence (pLDDT score)
   - Link to 3D structure viewer
   - Available experimental structures (PDB IDs, resolution, method)
   - Whether the protein is well-structured or has disordered regions
5. Use at most 3 tool calls (resolve + alphafold + pdb)
