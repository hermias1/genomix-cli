"""Deterministic output path generation."""
from pathlib import Path

OUTPUT_MAP = {
    "/qc": ("reports", "{sample}_fastqc.html"),
    "/align": ("data/processed", "{sample}.sorted.bam"),
    "/variant-call": ("data/processed", "{sample}.vcf.gz"),
    "/annotate": ("data/processed", "{sample}.annotated.vcf.gz"),
    "/blast": ("data/processed", "{sample}_blast_results.tsv"),
    "/msa": ("data/processed", "{sample}_alignment.fasta"),
    "/phylo": ("data/processed", "{sample}_tree.nwk"),
}

def output_path_for(command, input_file, project_root, override=None):
    if override: return override
    sample = Path(input_file).stem.split(".")[0]
    entry = OUTPUT_MAP.get(command)
    if not entry: return str(Path(project_root) / "data/processed" / sample)
    directory, template = entry
    return str(Path(project_root) / directory / template.format(sample=sample))
