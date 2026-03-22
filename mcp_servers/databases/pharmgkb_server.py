"""PharmGKB MCP server — pharmacogenomics (variant-drug interactions)."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("pharmgkb")
_server = BaseDatabaseServer(name="pharmgkb", base_url="https://api.pharmgkb.org/v1/data")


@mcp.tool()
def pharmgkb_variant(rsid: str) -> str:
    """Look up pharmacogenomic annotations for a variant by rsID.
    Returns drug interactions, clinical annotations, and dosing guidelines.
    Example: 'rs1045642' (affects response to many drugs)."""
    try:
        result = _server.get(f"variant/{rsid}", {"view": "base"})
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def pharmgkb_gene(symbol: str) -> str:
    """Look up pharmacogenomic information for a gene.
    Returns associated drugs, pathways, and clinical annotations.
    Example: 'CYP2D6', 'VKORC1'."""
    try:
        result = _server.get(f"gene/{symbol}", {"view": "base"})
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def pharmgkb_drug(drug_name: str) -> str:
    """Search PharmGKB for drug-gene interactions.
    Returns pharmacogenomic guidelines and variant associations.
    Example: 'warfarin', 'tamoxifen', 'clopidogrel'."""
    try:
        result = _server.get("drug", {"name": drug_name, "view": "base"})
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
