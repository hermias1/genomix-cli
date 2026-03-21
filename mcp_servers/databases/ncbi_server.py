"""NCBI Entrez MCP server for gene and sequence search."""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("ncbi")
_ncbi = BaseDatabaseServer(
    name="ncbi",
    base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
)


@mcp.tool()
def ncbi_search(database: str, query: str, max_results: int = 20) -> str:
    """Search an NCBI Entrez database and return matching IDs."""
    params = {"db": database, "term": query, "retmax": max_results, "retmode": "json"}
    try:
        result = _ncbi.get("esearch.fcgi", params)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def ncbi_fetch(database: str, ids: list[str], rettype: str = "gb", retmode: str = "text") -> str:
    """Fetch records from an NCBI Entrez database by IDs."""
    params = {"db": database, "id": ",".join(ids), "rettype": rettype, "retmode": retmode}
    try:
        result = _ncbi.get("efetch.fcgi", params)
        return result if isinstance(result, str) else json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def ncbi_summary(database: str, ids: list[str]) -> str:
    """Fetch document summaries from an NCBI Entrez database by IDs."""
    params = {"db": database, "id": ",".join(ids), "retmode": "json"}
    try:
        result = _ncbi.get("esummary.fcgi", params)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def ncbi_gene_info(gene_query: str) -> str:
    """Search NCBI Gene database and return summary for the top result."""
    params = {"db": "gene", "term": gene_query, "retmax": 1, "retmode": "json"}
    try:
        search_result = _ncbi.get("esearch.fcgi", params)
        ids = search_result.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return json.dumps({"error": "No gene found for query", "query": gene_query})
        summary_params = {"db": "gene", "id": ",".join(ids), "retmode": "json"}
        summary = _ncbi.get("esummary.fcgi", summary_params)
        return json.dumps(summary)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
