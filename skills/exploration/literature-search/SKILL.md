---
name: literature-search
description: Search PubMed for scientific articles about genes, variants, or diseases
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [literature, PubMed, research]
    tools_used: [pubmed_search, pubmed_gene_articles, pubmed_fetch_abstract]
---

# Literature Search

When the user asks about scientific literature:

1. **Search PubMed** using pubmed_search or pubmed_gene_articles
2. **For top results**, fetch abstracts if the user wants details
3. **Present** results with:
   - Title, authors, journal, year
   - PMID (for reference)
   - Brief summary of findings
4. Prioritize recent review articles and high-impact publications
5. Limit to 3-5 most relevant articles
