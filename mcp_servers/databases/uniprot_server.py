"""UniProt MCP server — protein information, function, domains, GO terms."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("uniprot")
_server = BaseDatabaseServer(name="uniprot", base_url="https://rest.uniprot.org")


@mcp.tool()
def uniprot_search(gene_name: str, organism: str = "human") -> str:
    """Search UniProt for a protein by gene name.
    Returns UniProt accession, protein name, function, and key annotations.
    Example: gene_name='TP53', organism='human'."""
    org_id = "9606" if organism.lower() in ("human", "homo sapiens") else organism
    try:
        result = _server.get("uniprotkb/search", {
            "query": f"gene_exact:{gene_name} AND organism_id:{org_id}",
            "format": "json",
            "size": "3",
            "fields": "accession,gene_names,protein_name,cc_function,ft_domain,length",
        })
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def uniprot_protein(accession: str) -> str:
    """Get detailed protein information by UniProt accession.
    Returns function, domains, GO terms, disease associations.
    Example: 'P04637' (TP53), 'P38398' (BRCA1)."""
    try:
        result = _server.get(f"uniprotkb/{accession}", {
            "format": "json",
            "fields": "accession,gene_names,protein_name,cc_function,cc_disease,ft_domain,go,xref_pfam,xref_interpro,length,sequence",
        })
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def uniprot_gene_to_accession(gene_name: str, organism: str = "human") -> str:
    """Resolve a gene name to its UniProt accession ID.
    Useful as a first step before querying AlphaFold or InterPro.
    Example: 'BRCA1' -> 'P38398'."""
    org_id = "9606" if organism.lower() in ("human", "homo sapiens") else organism
    try:
        result = _server.get("uniprotkb/search", {
            "query": f"gene_exact:{gene_name} AND organism_id:{org_id} AND reviewed:true",
            "format": "json",
            "size": "1",
            "fields": "accession,gene_names,protein_name",
        })
        if isinstance(result, dict):
            results = result.get("results", [])
            if results:
                entry = results[0]
                return json.dumps({
                    "accession": entry.get("primaryAccession", ""),
                    "gene": gene_name,
                    "protein_name": entry.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", ""),
                })
        return json.dumps({"error": f"No UniProt entry found for {gene_name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
