---
name: vcf-compare
description: Compare multiple VCF files — trio analysis, tumor-normal, cohort comparison
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [clinical, comparison, trio, tumor-normal, somatic]
    tools_used: [compare_vcfs, read_file]
---

# VCF Comparison

Compare 2-3 VCF files to find shared and unique variants.

## Use Cases

### Trio Analysis (child + two parents)
```
/compare child.vcf mother.vcf father.vcf
```
- **De novo mutations**: present in child, absent in BOTH parents
  → these are the most interesting for diagnosing genetic diseases in children
- **Compound heterozygous**: different variants in the same gene from each parent
  → relevant for autosomal recessive diseases
- **Inherited pathogenic**: known pathogenic variants inherited from a parent

### Tumor vs Normal
```
/compare tumor.vcf normal.vcf
```
- **Somatic mutations**: present in tumor, absent in normal tissue
  → these are the cancer driver candidates
- **Germline variants**: shared between tumor and normal
  → inherited predisposition

### Cohort Comparison
```
/compare patient1.vcf patient2.vcf
```
- Shared variants between patients
- Unique variants to each

## Analysis Steps

1. Use **compare_vcfs** tool with the provided files
2. Report summary: total variants, shared, unique to each
3. For trio: highlight de novo mutations with gene names
4. For tumor/normal: highlight somatic variants, especially in cancer genes
5. Interpret the most significant findings
