"""dbSNP MCP server for SNP search via NCBI Entrez."""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("dbsnp")
_ncbi = BaseDatabaseServer(
    name="dbsnp",
    base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
)


@mcp.tool()
def dbsnp_search(query: str) -> str:
    """Search dbSNP for variants matching a query."""
    params = {"db": "snp", "term": query, "retmax": 5, "retmode": "json"}
    try:
        result = _ncbi.get("esearch.fcgi", params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def dbsnp_fetch(rs_ids: list[str]) -> str:
    """Fetch dbSNP records by rs IDs."""
    params = {"db": "snp", "id": ",".join(rs_ids), "rettype": "json", "retmode": "text"}
    try:
        result = _ncbi.get("efetch.fcgi", params)
        text = result if isinstance(result, str) else json.dumps(result)
        return text[:2000] + "... [truncated]" if len(text) > 2000 else text
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def dbsnp_summary(rs_ids: list[str]) -> str:
    """Fetch dbSNP document summaries by rs IDs."""
    params = {"db": "snp", "id": ",".join(rs_ids), "retmode": "json"}
    try:
        result = _ncbi.get("esummary.fcgi", params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
