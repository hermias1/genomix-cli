---
name: genome-references
description: Choose between GRCh38 and GRCh37, perform coordinate liftover, and select organism-specific references
version: 1.0.0
author: genomix-cli
license: Apache-2.0
metadata:
  genomix:
    tags: [common, references, GRCh38, GRCh37, hg38, hg19, liftover, assembly]
    tools_used: [run_command, ncbi_search]
---

# Genome Reference Selection

## GRCh38 vs GRCh37

| Feature | GRCh37 (hg19) | GRCh38 (hg38) |
|---------|---------------|----------------|
| Release | 2009 | 2013 (last patch 2022) |
| Alternate loci | None | 261 ALT sequences |
| Centromere resolution | Incomplete | Near-complete |
| Annotation currency | Legacy databases | Active updates (GENCODE, RefSeq) |
| Clinical databases | ClinVar legacy data | Current default |
| Chromosome names | chr1–22, chrX, chrY | chr1–22, chrX, chrY (same) |

**Use GRCh38** for all new projects. GRCh37 is only justified when:
- Reanalyzing legacy data that must remain comparable to a previous GRCh37 run.
- A clinical database or variant report explicitly uses GRCh37 coordinates.
- A collaboration partner mandates GRCh37.

Note: UCSC names (hg19/hg38) are interchangeable with Ensembl/NCBI names (GRCh37/GRCh38) for the primary assembly — the sequences are identical.

## Coordinate Liftover

To convert coordinates from GRCh37 to GRCh38 (or reverse), use UCSC liftOver or Picard LiftoverVcf.

### liftOver (BED)

```bash
# Download chain file
wget https://hgdownload.soe.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg38.over.chain.gz

liftOver \
  input.hg19.bed \
  hg19ToHg38.over.chain.gz \
  output.hg38.bed \
  unmapped.bed
```

### Picard LiftoverVcf

```bash
gatk LiftoverVcf \
  -I sample.hg19.vcf.gz \
  -O sample.hg38.vcf.gz \
  --CHAIN hg19ToHg38.over.chain.gz \
  -R GRCh38.fa \
  --REJECT rejected.vcf.gz
```

Always inspect the `unmapped.bed` or `rejected.vcf.gz` — coordinates in regions that were restructured between assemblies cannot be lifted over reliably.

## Common Organism References

| Organism | Assembly | NCBI Accession |
|----------|----------|----------------|
| Human | GRCh38.p14 | GCA_000001405.29 |
| Mouse | GRCm39 | GCA_000001635.9 |
| Zebrafish | GRCz11 | GCA_000002035.4 |
| Drosophila | dm6 | GCA_000001215.4 |
| C. elegans | WBcel235 | GCA_000002985.3 |
| E. coli K-12 | ASM584v2 | GCA_000005845.2 |
| SARS-CoV-2 | ASM985889v3 | GCA_009858895.3 |
| Arabidopsis | TAIR10.1 | GCA_000001735.2 |

## Reference Download

```bash
# Human GRCh38 from NCBI
wget https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/001/405/GCA_000001405.15_GRCh38/GCA_000001405.15_GRCh38_assembly_structure/Primary_Assembly/assembled_chromosomes/FASTA/chroms.tar.gz

# Or via Ensembl (soft-masked)
wget https://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz
```

Ensembl FASTA uses chromosome names without `chr` prefix (e.g., `1`, `X`). UCSC/NCBI FASTAs use `chr1`, `chrX`. Ensure the chromosome naming convention matches your annotation files to avoid silently skipping records.
