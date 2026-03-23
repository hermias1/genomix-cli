---
name: protein-structure
description: Analyze protein structure predictions and their implications for variant interpretation
version: 2.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [protein, structure, AlphaFold, PDB, AlphaMissense]
    tools_used: [uniprot_gene_to_accession, alphafold_prediction, alphafold_confidence, pdb_search_gene, interpro_protein]
---

# Protein Structure Analysis

When the user asks about protein structure:

1. **Resolve gene → UniProt ID** (uniprot_gene_to_accession)
2. **AlphaFold prediction**:
   - Overall confidence (global pLDDT)
   - Fraction of well-structured vs disordered regions
   - Link to 3D viewer
3. **Experimental structures** (pdb_search_gene):
   - Number of PDB structures available
   - Best resolution
   - What parts of the protein have been crystallized
4. **Protein domains** (interpro_protein):
   - Functional domains and their positions
   - Active sites, binding sites
5. **Clinical relevance**:
   - Which domains are critical for function?
   - Where do pathogenic variants cluster?
   - AlphaMissense: which regions are intolerant to missense changes?

Explain structural biology concepts in accessible terms:
- pLDDT > 90 = "very high confidence — this region has a well-defined 3D structure"
- pLDDT 70-90 = "confident — structure is reliable"
- pLDDT < 50 = "disordered — this region is flexible/unstructured"

Use at most 3-4 tool calls (resolve + alphafold + pdb or interpro).
