"""OMIM MCP server — genetic disease and gene-phenotype relationships."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("omim")
_ncbi = BaseDatabaseServer(name="omim", base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils")


@mcp.tool()
def omim_search(query: str, max_results: int = 5) -> str:
    """Search OMIM for genetic diseases or gene-phenotype relationships.
    Example queries: 'BRCA1', 'breast cancer hereditary', 'cystic fibrosis'."""
    params = {"db": "omim", "term": query, "retmax": max_results, "retmode": "json"}
    try:
        result = _ncbi.get("esearch.fcgi", params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def omim_summary(omim_ids: list[str]) -> str:
    """Get OMIM entry summaries by MIM numbers."""
    params = {"db": "omim", "id": ",".join(omim_ids[:5]), "retmode": "json"}
    try:
        result = _ncbi.get("esummary.fcgi", params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def omim_gene_disease(gene_symbol: str) -> str:
    """Find diseases associated with a gene in OMIM.
    Returns MIM numbers and disease names for the given gene."""
    params = {"db": "omim", "term": f"{gene_symbol}[Gene]", "retmax": 10, "retmode": "json"}
    try:
        search = _ncbi.get("esearch.fcgi", params)
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return json.dumps({"error": f"No OMIM entries found for {gene_symbol}"})
        summary_params = {"db": "omim", "id": ",".join(ids[:5]), "retmode": "json"}
        result = _ncbi.get("esummary.fcgi", summary_params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
