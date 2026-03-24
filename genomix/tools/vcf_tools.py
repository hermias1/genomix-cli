"""VCF analysis tools — compare, filter, and prioritize variants."""
import json
from pathlib import Path
from typing import Any

from genomix.gene_db import get_gene_db


def _parse_vcf_variants(path: str) -> list[dict]:
    """Parse a VCF file and return variant dicts with gene annotations."""
    db = get_gene_db()
    db.ensure_loaded()

    variants = []
    p = Path(path).expanduser()
    if not p.exists():
        return []

    import gzip
    opener = gzip.open if p.suffix in (".gz", ".bgz") else open
    with opener(p, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            fields = line.strip().split("\t")
            if len(fields) < 5:
                continue
            chrom, pos, vid, ref, alt = fields[0], fields[1], fields[2], fields[3], fields[4]

            # Get gene from local DB
            genes = db.lookup(chrom, int(pos))
            gene = genes[0] if genes else "unknown"

            # Parse INFO for annotations
            info = fields[7] if len(fields) > 7 else "."
            clnsig = ""
            if "CLNSIG=" in info:
                for part in info.split(";"):
                    if part.startswith("CLNSIG="):
                        clnsig = part.split("=")[1]

            # Determine variant type
            if len(ref) == 1 and len(alt) == 1:
                vtype = "SNV"
            elif len(ref) > len(alt):
                vtype = "deletion"
            elif len(ref) < len(alt):
                vtype = "insertion"
            else:
                vtype = "complex"

            # Parse genotype if present
            gt = ""
            if len(fields) > 9:
                gt_field = fields[9].split(":")[0]
                if gt_field == "0/1" or gt_field == "0|1":
                    gt = "heterozygous"
                elif gt_field == "1/1" or gt_field == "1|1":
                    gt = "homozygous"

            variants.append({
                "chrom": chrom, "pos": int(pos), "ref": ref, "alt": alt,
                "gene": gene, "type": vtype, "genotype": gt,
                "significance": clnsig, "id": vid,
            })
    return variants


def compare_vcfs(args: dict) -> str:
    """Compare 2-3 VCF files and find shared/unique variants.

    Args: file1, file2, file3 (optional)
    Returns: JSON with shared variants, unique to each file, and summary.
    """
    file1 = args.get("file1", "")
    file2 = args.get("file2", "")
    file3 = args.get("file3", "")

    v1 = _parse_vcf_variants(file1)
    v2 = _parse_vcf_variants(file2)
    v3 = _parse_vcf_variants(file3) if file3 else []

    def var_key(v):
        return f"{v['chrom']}:{v['pos']}:{v['ref']}>{v['alt']}"

    keys1 = {var_key(v) for v in v1}
    keys2 = {var_key(v) for v in v2}
    keys3 = {var_key(v) for v in v3} if v3 else set()

    shared_12 = keys1 & keys2
    only_1 = keys1 - keys2
    only_2 = keys2 - keys1

    result = {
        "file1": {"path": file1, "total_variants": len(v1)},
        "file2": {"path": file2, "total_variants": len(v2)},
        "shared": len(shared_12),
        "unique_to_file1": len(only_1),
        "unique_to_file2": len(only_2),
    }

    # Include gene names for unique variants (most interesting)
    def variants_for_keys(variants, keys, limit=20):
        return [
            {"gene": v["gene"], "variant": f"{v['chrom']}:{v['pos']} {v['ref']}>{v['alt']}", "type": v["type"]}
            for v in variants if var_key(v) in keys
        ][:limit]

    result["unique_to_file1_variants"] = variants_for_keys(v1, only_1)
    result["unique_to_file2_variants"] = variants_for_keys(v2, only_2)

    if file3:
        keys_all = keys1 & keys2 & keys3
        result["file3"] = {"path": file3, "total_variants": len(v3)}
        result["shared_all_three"] = len(keys_all)

        # De novo: in file3 (child) but not in file1 (parent1) or file2 (parent2)
        de_novo = keys3 - keys1 - keys2
        result["de_novo_in_file3"] = len(de_novo)
        result["de_novo_variants"] = variants_for_keys(v3, de_novo)

    return json.dumps(result, indent=2)


def filter_vcf(args: dict) -> str:
    """Filter and prioritize variants from a VCF file.

    Args:
        path: VCF file path
        genes: comma-separated gene list to filter (optional)
        types: comma-separated variant types to keep (optional: SNV,deletion,insertion)
        exclude_common: if "true", exclude variants with known benign classification
    Returns: JSON with filtered variants and summary.
    """
    path = args.get("path", "")
    gene_filter = set(g.strip() for g in args.get("genes", "").split(",") if g.strip())
    type_filter = set(t.strip() for t in args.get("types", "").split(",") if t.strip())
    exclude_common = args.get("exclude_common", "false").lower() == "true"

    variants = _parse_vcf_variants(path)
    filtered = []

    for v in variants:
        if gene_filter and v["gene"] not in gene_filter:
            continue
        if type_filter and v["type"] not in type_filter:
            continue
        if exclude_common and v["significance"].lower() in ("benign", "likely_benign"):
            continue
        filtered.append(v)

    # Group by gene
    by_gene = {}
    for v in filtered:
        g = v["gene"]
        if g not in by_gene:
            by_gene[g] = []
        by_gene[g].append(v)

    return json.dumps({
        "total_input": len(variants),
        "total_filtered": len(filtered),
        "genes_affected": list(by_gene.keys()),
        "variants_by_gene": {g: vs[:10] for g, vs in by_gene.items()},
        "filters_applied": {
            "genes": list(gene_filter) if gene_filter else "all",
            "types": list(type_filter) if type_filter else "all",
            "exclude_common": exclude_common,
        },
    }, indent=2)


def register_vcf_tools(registry):
    """Register VCF analysis tools."""
    registry.register(
        name="compare_vcfs",
        description="Compare 2-3 VCF files. Find shared/unique variants. For trios: finds de novo mutations (in child but not parents).",
        parameters={
            "type": "object",
            "properties": {
                "file1": {"type": "string", "description": "Path to first VCF file"},
                "file2": {"type": "string", "description": "Path to second VCF file"},
                "file3": {"type": "string", "description": "Path to third VCF file (optional, for trio analysis)"},
            },
            "required": ["file1", "file2"],
        },
        handler=compare_vcfs,
    )
    registry.register(
        name="filter_vcf",
        description="Filter and prioritize variants from a VCF. Filter by gene list, variant type, or exclude common/benign variants.",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to VCF file"},
                "genes": {"type": "string", "description": "Comma-separated gene list to filter (e.g. 'BRCA1,BRCA2,TP53')"},
                "types": {"type": "string", "description": "Variant types to keep (e.g. 'SNV,deletion')"},
                "exclude_common": {"type": "string", "description": "Set to 'true' to exclude benign/likely_benign variants"},
            },
            "required": ["path"],
        },
        handler=filter_vcf,
    )
