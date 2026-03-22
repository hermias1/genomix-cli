"""COSMIC MCP server — somatic cancer mutations."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("cosmic")
_ncbi = BaseDatabaseServer(name="cosmic", base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils")


@mcp.tool()
def cosmic_search_gene(gene_symbol: str) -> str:
    """Search for somatic cancer mutations in a gene using NCBI/ClinVar cancer data.
    Returns known pathogenic somatic variants for the gene.
    Example: 'TP53', 'KRAS', 'BRAF'."""
    params = {"db": "clinvar", "term": f"{gene_symbol}[Gene] AND somatic[Origin]", "retmax": 10, "retmode": "json"}
    try:
        search = _ncbi.get("esearch.fcgi", params)
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return json.dumps({"info": f"No somatic variants found for {gene_symbol}", "gene": gene_symbol})
        summary_params = {"db": "clinvar", "id": ",".join(ids[:5]), "retmode": "json"}
        result = _ncbi.get("esummary.fcgi", summary_params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def cosmic_search_variant(variant_description: str) -> str:
    """Search for a specific somatic variant in cancer databases.
    variant_description can be an rsID, HGVS notation, or gene+mutation.
    Example: 'BRAF V600E', 'rs113488022', 'KRAS G12D'."""
    params = {"db": "clinvar", "term": f"{variant_description} AND somatic[Origin]", "retmax": 5, "retmode": "json"}
    try:
        search = _ncbi.get("esearch.fcgi", params)
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return json.dumps({"info": f"No results for '{variant_description}'", "query": variant_description})
        summary_params = {"db": "clinvar", "id": ",".join(ids[:5]), "retmode": "json"}
        result = _ncbi.get("esummary.fcgi", summary_params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def cosmic_cancer_genes(cancer_type: str = "") -> str:
    """Search for genes associated with a specific cancer type.
    Example: 'breast cancer', 'melanoma', 'lung adenocarcinoma'."""
    term = f"{cancer_type} AND somatic[Origin]" if cancer_type else "somatic[Origin]"
    params = {"db": "clinvar", "term": term, "retmax": 10, "retmode": "json"}
    try:
        result = _ncbi.get("esearch.fcgi", params)
        return _ncbi.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
