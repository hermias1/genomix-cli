"""InterPro MCP server — protein domains, families, and functional annotations."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("interpro")
_server = BaseDatabaseServer(name="interpro", base_url="https://www.ebi.ac.uk/interpro/api")


@mcp.tool()
def interpro_protein(uniprot_id: str) -> str:
    """Get protein domain annotations from InterPro for a UniProt accession.
    Returns protein families, domains, and functional sites.
    Example: 'P38398' (BRCA1), 'P04637' (TP53)."""
    try:
        result = _server.get(f"protein/uniprot/{uniprot_id}", {"format": "json"})
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def interpro_entry(entry_id: str) -> str:
    """Get details about an InterPro entry (domain, family, or site).
    Example: 'IPR011364' (BRCA1 DNA-binding domain)."""
    try:
        result = _server.get(f"entry/interpro/{entry_id}", {"format": "json"})
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def interpro_search(query: str) -> str:
    """Search InterPro for protein domains or families matching a query.
    Example: 'DNA repair', 'kinase domain', 'tumor suppressor'."""
    try:
        result = _server.get("entry/interpro", {"search": query, "format": "json", "page_size": "5"})
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
