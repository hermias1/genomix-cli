"""PubMed MCP server — biomedical literature search."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("pubmed")
_ncbi = BaseDatabaseServer(name="pubmed", base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils")


@mcp.tool()
def pubmed_search(query: str, max_results: int = 5) -> str:
    """Search PubMed for scientific articles.
    Returns article titles, authors, and PubMed IDs.
    Example: 'BRCA1 breast cancer risk', 'rs334 sickle cell'."""
    params = {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json", "sort": "relevance"}
    try:
        search = _ncbi.get("esearch.fcgi", params)
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return json.dumps({"info": f"No articles found for '{query}'"})
        summary_params = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
        result = _ncbi.get("esummary.fcgi", summary_params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def pubmed_fetch_abstract(pmid: str) -> str:
    """Fetch the abstract of a PubMed article by PMID.
    Example: '12345678'."""
    params = {"db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "text"}
    try:
        result = _ncbi.get("efetch.fcgi", params)
        text = result if isinstance(result, str) else json.dumps(result)
        return text[:2000] + "... [truncated]" if len(text) > 2000 else text
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def pubmed_gene_articles(gene_symbol: str, max_results: int = 5) -> str:
    """Find recent articles about a specific gene.
    Example: 'TP53', 'CFTR', 'APOE'."""
    params = {"db": "pubmed", "term": f"{gene_symbol}[Gene] AND review[pt]", "retmax": max_results, "retmode": "json", "sort": "date"}
    try:
        search = _ncbi.get("esearch.fcgi", params)
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return json.dumps({"info": f"No articles found for gene {gene_symbol}"})
        summary_params = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
        result = _ncbi.get("esummary.fcgi", summary_params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
