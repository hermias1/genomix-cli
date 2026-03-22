"""Ensembl REST API MCP server for gene and variant lookup."""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("ensembl")
_ensembl = BaseDatabaseServer(
    name="ensembl",
    base_url="https://rest.ensembl.org",
)


@mcp.tool()
def ensembl_lookup_gene(species: str, symbol: str) -> str:
    """Look up an Ensembl gene by species and gene symbol."""
    params = {"content-type": "application/json"}
    try:
        result = _ensembl.get(f"xrefs/symbol/{species}/{symbol}", params)
        return _ensembl.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def ensembl_get_sequence(id: str, type: str = "genomic") -> str:
    """Retrieve sequence for an Ensembl ID."""
    params = {"content-type": "application/json", "type": type}
    try:
        result = _ensembl.get(f"sequence/id/{id}", params)
        return _ensembl.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def ensembl_vep(species: str, hgvs_notation: str) -> str:
    """Run Variant Effect Predictor (VEP) for a variant in HGVS notation."""
    params = {"content-type": "application/json"}
    try:
        result = _ensembl.get(f"vep/{species}/hgvs/{hgvs_notation}", params)
        return _ensembl.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def ensembl_variant_info(species: str, variant_id: str) -> str:
    """Retrieve information about a variant by Ensembl variant ID."""
    params = {"content-type": "application/json"}
    try:
        result = _ensembl.get(f"variation/{species}/{variant_id}", params)
        return _ensembl.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def ensembl_population_frequencies(species: str, variant_id: str) -> str:
    """Get population allele frequencies for a variant (gnomAD/1000 Genomes).

    Returns frequency data across populations: AFR (African), EUR (European),
    EAS (East Asian), SAS (South Asian), AMR (American). Useful for ancestry inference.
    variant_id should be an rsID like 'rs334'.
    """
    params = {"content-type": "application/json", "population_genotypes": "1"}
    try:
        result = _ensembl.get(f"variation/{species}/{variant_id}", params)
        # Extract just the population data to keep it compact
        if isinstance(result, dict):
            populations = result.get("populations", [])
            # Filter to major populations only
            major_pops = {}
            for pop in populations[:50]:
                pop_name = pop.get("population", "")
                if any(k in pop_name for k in ["gnomAD", "1000GENOMES"]):
                    freq = pop.get("frequency")
                    if freq is not None:
                        major_pops[pop_name] = freq
            summary = {
                "variant": variant_id,
                "clinical_significance": result.get("clinical_significance", []),
                "most_severe_consequence": result.get("most_severe_consequence", ""),
                "ancestral_allele": result.get("ancestral_allele", ""),
                "minor_allele": result.get("minor_allele", ""),
                "maf": result.get("MAF", ""),
                "population_frequencies": dict(list(major_pops.items())[:20]),
            }
            return json.dumps(summary)
        return _ensembl.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
