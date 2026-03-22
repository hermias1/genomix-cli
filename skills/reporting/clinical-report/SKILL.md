---
name: clinical-report
description: Generate a structured clinical variant report from a VCF file
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [reporting, clinical, variants, oncogenetics]
    tools_used: [read_file, clinvar_search, ensembl_variant_info]
---

# Clinical Variant Report Generation

When the user asks for a clinical report on a VCF file:

1. **Read the VCF file** using read_file
2. **Identify each variant**: gene, position, ref/alt, effect, clinical significance
3. **For each variant**, provide:
   - Gene name and function
   - Variant type (missense, nonsense, frameshift, etc.)
   - Zygosity (heterozygous 0/1 or homozygous 1/1)
   - Clinical significance (Pathogenic, Likely pathogenic, VUS, Benign, Risk factor)
   - Disease association
4. **Respond with a JSON block** in exactly this format (the system will parse it):

```json
{
  "variants": [
    {
      "gene": "BRCA1",
      "variant": "chr17:43094464 G>A (rs80357906)",
      "type": "missense_variant",
      "zygosity": "Heterozygous",
      "significance": "Pathogenic"
    }
  ],
  "interpretation": "<p>Clinical interpretation text with HTML formatting...</p>",
  "recommendations": "<div class='recommendation'>Recommendation text...</div>"
}
```

IMPORTANT:
- Use HTML tags in interpretation and recommendations (p, ul, li, strong, div class='recommendation')
- List ALL variants from the file, not just a subset
- Use your knowledge of well-known variants at known genomic positions
- Keep interpretation concise but clinically relevant
- Include carrier status for recessive conditions
- Flag actionable variants (cancer risk, pharmacogenomics)
