---
name: pgx-profile
description: Generate a complete pharmacogenomics profile from a VCF file
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [pharmacogenomics, PGx, drug-response, clinical]
    tools_used: [read_file, pharmgkb_gene, pharmgkb_variant]
---

# Pharmacogenomics Profile

Generate a comprehensive pharmacogenomics (PGx) profile from a VCF file.

## Key Pharmacogenes to Check

Scan the VCF for variants in these clinically actionable pharmacogenes:

| Gene | Chromosome | Drugs Affected | Clinical Impact |
|------|-----------|----------------|-----------------|
| CYP2D6 | chr22:42,126,499-42,130,881 | Tamoxifen, codeine, tramadol, antidepressants | Metabolizer status |
| CYP2C19 | chr10:94,762,681-94,855,547 | Clopidogrel, omeprazole, voriconazole | Metabolizer status |
| CYP2C9 | chr10:94,938,657-94,990,091 | Warfarin, phenytoin, NSAIDs | Metabolizer status |
| DPYD | chr1:97,543,299-97,912,700 | 5-FU, capecitabine | CRITICAL: toxicity risk |
| VKORC1 | chr16:31,096,068-31,099,845 | Warfarin | Dose sensitivity |
| TPMT | chr6:18,128,542-18,155,374 | 6-mercaptopurine, azathioprine | Toxicity risk |
| UGT1A1 | chr2:233,757,013-233,773,299 | Irinotecan | Toxicity risk |
| NUDT15 | chr13:48,037,987-48,052,553 | 6-mercaptopurine, azathioprine | Toxicity risk |
| SLCO1B1 | chr12:21,283,663-21,394,730 | Simvastatin, other statins | Myopathy risk |
| CYP3A5 | chr7:99,648,193-99,679,998 | Tacrolimus | Dose adjustment |

## Analysis Steps

1. **Read the VCF** and identify variants in pharmacogenes (use [GENE:] tags)
2. **For each pharmacogene found**:
   - Identify the specific variant(s)
   - Determine the likely star allele or functional impact
   - Predict metabolizer status (ultrarapid/rapid/normal/intermediate/poor)
   - List affected drugs and clinical recommendations
3. **Flag CRITICAL alerts** (red): DPYD deficiency before fluoropyrimidines is life-threatening
4. **Summary table** with: Gene | Variant | Predicted Phenotype | Drugs | Action

## Important Notes
- If no pharmacogene variants are found, say so — it likely means normal metabolizer status
- Always note that PGx interpretation requires clinical validation
- DPYD variants before 5-FU/capecitabine: this is literally life-or-death — always highlight
- Use PharmGKB tools to verify drug-gene interactions when possible (but don't over-query)
