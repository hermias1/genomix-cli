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
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def ensembl_get_sequence(id: str, type: str = "genomic") -> str:
    """Retrieve sequence for an Ensembl ID."""
    params = {"content-type": "application/json", "type": type}
    try:
        result = _ensembl.get(f"sequence/id/{id}", params)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def ensembl_vep(species: str, hgvs_notation: str) -> str:
    """Run Variant Effect Predictor (VEP) for a variant in HGVS notation."""
    params = {"content-type": "application/json"}
    try:
        result = _ensembl.get(f"vep/{species}/hgvs/{hgvs_notation}", params)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def ensembl_variant_info(species: str, variant_id: str) -> str:
    """Retrieve information about a variant by Ensembl variant ID."""
    params = {"content-type": "application/json"}
    try:
        result = _ensembl.get(f"variation/{species}/{variant_id}", params)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
