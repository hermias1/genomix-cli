---
name: database-search
description: Design effective NCBI and Ensembl search strategies and combine results across genomic databases
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [exploration, ncbi, ensembl, database, search, entrez]
    tools_used: [ncbi_search, ensembl_search, web_fetch]
---

# Genomic Database Search Strategies

## NCBI Search (Entrez)

NCBI Entrez covers: nucleotide, protein, gene, SNP (dbSNP), ClinVar, SRA, PubMed, and more.

### Effective Query Syntax

Use field tags to narrow results:

```
BRCA1[Gene Name] AND Homo sapiens[Organism] AND pathogenic[CLNSIG]
```

Common field tags:
- `[Gene Name]` — official HGNC symbol.
- `[Organism]` — full species name or NCBI taxonomy ID: `9606[Taxonomy ID]`.
- `[Title]` — restrict to terms in the record title.
- `[ACCN]` — search by accession number directly.
- `[SLEN]` — sequence length filter: `200:500[SLEN]` for 200–500 bp sequences.

### Database-Specific Tips

**Nucleotide/GenBank**: Add `AND complete genome[Title]` for whole genomes. Use `RefSeq[Filter]` to restrict to curated entries.

**SRA**: Search by experiment type: `WGS[Strategy] AND Homo sapiens[Organism]`. Filter by platform: `ILLUMINA[Platform]`.

**ClinVar**: Combine variant and gene: `NM_007294[Accession] AND pathogenic[Clinical Significance]`. Check review status stars.

**dbSNP**: Search by rsID (`rs28897696`) or by gene and consequence (`BRCA1 AND missense`).

## Ensembl Search

Ensembl provides genome browser, gene models, and variation data with a REST API.

```
https://rest.ensembl.org/lookup/symbol/homo_sapiens/BRCA1?content-type=application/json
```

Useful Ensembl REST endpoints:
- `/lookup/symbol/<species>/<gene>` — gene coordinates and stable ID.
- `/variation/<species>/<rsid>` — variant details, consequences.
- `/sequence/region/<species>/<region>` — fetch sequence for a genomic region.
- `/overlap/region/<species>/<region>?feature=gene` — all genes in a region.

## Combining Databases

For a comprehensive variant lookup, query in this order:
1. **ClinVar**: clinical significance and supporting evidence.
2. **dbSNP**: population frequency from gnomAD/1000 Genomes if available.
3. **Ensembl VEP**: consequence predictions and regulatory overlap.
4. **OMIM**: gene-disease relationship and inheritance pattern.
5. **UniProt**: protein function, domains, and known disease mutations.

When databases disagree on classification, prefer ClinVar entries with ≥2 gold stars over single-submitter records, and note the discrepancy in the report.

## Rate Limits

- NCBI Entrez: 3 requests/second without API key; 10/second with key (set `NCBI_API_KEY` env var).
- Ensembl REST: 15 requests/second; use POST for batch queries.
- Always add retry logic with exponential backoff for automated pipelines.
