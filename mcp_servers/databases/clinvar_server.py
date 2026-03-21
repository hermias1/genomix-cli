"""ClinVar MCP server for clinical variant search via NCBI Entrez."""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("clinvar")
_ncbi = BaseDatabaseServer(
    name="clinvar",
    base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
)


@mcp.tool()
def clinvar_search(query: str) -> str:
    """Search ClinVar for variants matching a query (rsID, gene name, etc.)."""
    params = {"db": "clinvar", "term": query, "retmax": 5, "retmode": "json"}
    try:
        result = _ncbi.get("esearch.fcgi", params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def clinvar_fetch(variant_ids: list[str]) -> str:
    """Fetch ClinVar records by variant IDs."""
    params = {"db": "clinvar", "id": ",".join(variant_ids[:5]), "rettype": "clinvarset", "retmode": "xml"}
    try:
        result = _ncbi.get("efetch.fcgi", params)
        text = result if isinstance(result, str) else json.dumps(result)
        return text[:2000] + "... [truncated]" if len(text) > 2000 else text
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def clinvar_summary(variant_ids: list[str]) -> str:
    """Fetch ClinVar document summaries by variant IDs."""
    params = {"db": "clinvar", "id": ",".join(variant_ids[:5]), "retmode": "json"}
    try:
        result = _ncbi.get("esummary.fcgi", params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
