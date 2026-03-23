---
name: population-frequency
description: Look up population allele frequencies from gnomAD
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [population, frequency, gnomAD, ancestry]
    tools_used: [gnomad_variant, ensembl_population_frequencies]
---

# Population Frequency Lookup

When the user asks about variant frequency in populations:

1. **Query gnomAD** using gnomad_variant for allele frequencies
2. **Also try** ensembl_population_frequencies for additional data
3. **Present** frequency data across populations:
   - Global allele frequency
   - AFR (African/African-American)
   - EUR (European non-Finnish)
   - EAS (East Asian)
   - SAS (South Asian)
   - AMR (Admixed American)
   - ASJ (Ashkenazi Jewish)
   - FIN (Finnish)
4. **Interpret**: rare (<1%), low frequency (1-5%), common (>5%)
5. Discuss implications for variant classification (ACMG BA1/BS1 criteria)
