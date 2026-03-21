---
name: blast-analysis
description: Select the correct BLAST program (blastn/blastp/blastx), set e-value thresholds, and interpret results
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [comparative, blast, blastn, blastp, blastx, similarity, e-value]
    tools_used: [run_blast, ncbi_search]
---

# BLAST Analysis

## Program Selection

| Query | Database | Program |
|-------|----------|---------|
| Nucleotide | Nucleotide | blastn |
| Protein | Protein | blastp |
| Nucleotide (translated) | Protein | blastx |
| Protein | Nucleotide (translated) | tblastn |
| Nucleotide (translated) | Nucleotide (translated) | tblastx |

Decision rules:
- **blastn**: Comparing closely related sequences (same species, >70% identity), primer design, confirming PCR products.
- **blastp**: Comparing protein sequences across species, finding orthologs, functional domain analysis.
- **blastx**: Annotating novel nucleotide sequences (EST, genome contig) — finds protein homologs in 6-frame translation.
- **tblastn**: Finding gene locations in an unannotated genome assembly using a known protein query.

Avoid tblastx for large queries — it is computationally expensive.

## E-value Interpretation

The e-value (expect value) is the number of alignments of equal or better score expected by chance in a database of this size.

| E-value | Interpretation |
|---------|----------------|
| < 1e-100 | Nearly identical sequences (>95% identity at full length) |
| 1e-50 to 1e-100 | Very strong homology, high confidence |
| 1e-10 to 1e-50 | Significant homology, likely true hit |
| 1e-3 to 1e-10 | Moderate confidence, check alignment manually |
| 0.01 to 1 | Weak hit, may be spurious — check length and identity |
| > 1 | Likely noise, not significant |

Default e-value cutoff is 10. For genomics, use `1e-5` as a starting filter; tighten to `1e-20` for confident functional annotation.

## Key Result Fields

- **% identity**: Fraction of aligned positions with exact match.
- **query coverage**: Fraction of the query sequence in the alignment. Low coverage (<50%) with high identity often means domain hit rather than full-length homolog.
- **bit score**: Normalized score independent of database size — use for ranking across runs.
- **gaps**: High gap content with moderate identity may indicate divergent or frameshifted sequences.

## Local BLAST Command Example

```bash
# Build local database
makeblastdb -in proteins.fasta -dbtype prot -out mydb

# Run blastp
blastp \
  -query query.fasta \
  -db mydb \
  -out results.txt \
  -evalue 1e-10 \
  -outfmt "6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore" \
  -num_threads 8 \
  -max_target_seqs 10
```

Format 6 (tabular) is easiest for downstream filtering. Always specify `-max_target_seqs` to avoid memory issues with large databases.
