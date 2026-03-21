---
name: phylogenetics
description: Build phylogenetic trees with FastTree, interpret Newick format, and assess bootstrap support
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [comparative, phylogenetics, fasttree, newick, tree-building]
    tools_used: [run_command, read_file]
---

# Phylogenetic Tree Building with FastTree

## When to Use FastTree

FastTree approximates maximum-likelihood (ML) trees using neighbor-joining for an initial topology, then applies NNI (nearest-neighbor interchange) and SPR (subtree pruning/regrafting) moves. It is orders of magnitude faster than RAxML or IQ-TREE for large datasets (>500 sequences).

Use FastTree when:
- You have >200 sequences and need a result in minutes.
- You need a quick exploratory tree before committing to a slower, more thorough method.

Use IQ-TREE or RAxML when:
- Accuracy is paramount (publication-quality tree with model selection).
- Dataset is <500 sequences and run time is not a constraint.

## Input Requirements

FastTree requires a multiple sequence alignment in FASTA or PHYLIP format. Always trim the alignment first (see multiple-alignment skill).

## Commands

```bash
# Nucleotide alignment (GTR+CAT model — default for DNA)
FastTree -gtr -nt trimmed.fasta > tree.nwk

# Protein alignment (WAG model)
FastTree trimmed.fasta > tree.nwk

# With 1000 bootstrap replicates (slower but adds confidence values)
FastTree -gtr -nt -boot 1000 trimmed.fasta > tree.nwk
```

## Newick Format

A Newick tree encodes topology and branch lengths as nested parentheses:

```
((A:0.1,B:0.2):0.05,(C:0.3,D:0.15):0.08);
```

- Each leaf is a sequence identifier.
- Numbers after `:` are branch lengths (substitutions per site).
- Numbers before `:` at internal nodes are bootstrap values (0–1 for FastTree; 0–100 for RAxML/IQ-TREE).
- The semicolon terminates the tree.

## Interpreting Bootstrap Support

| Value (0–1 scale) | Interpretation |
|-------------------|----------------|
| ≥ 0.95 | Strong support — clade is well-resolved |
| 0.70–0.94 | Moderate support — likely correct |
| 0.50–0.69 | Weak support — treat with caution |
| < 0.50 | Unresolved — do not over-interpret the clade |

## Visualization

Convert and visualize Newick trees with:
- **FigTree** (GUI, free): color branches by bootstrap, midpoint-root.
- **iTOL** (web): publication-quality with metadata overlays.
- **ETE3** (Python): programmatic rendering.

```python
from ete3 import Tree
t = Tree("tree.nwk")
print(t.get_ascii(show_internal=True))
```

Always root the tree at an outgroup or by midpoint before interpreting topology.
