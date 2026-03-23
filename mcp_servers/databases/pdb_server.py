"""RCSB PDB MCP server — experimental protein structures."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer
import httpx

mcp = FastMCP("pdb")
_data = BaseDatabaseServer(name="pdb_data", base_url="https://data.rcsb.org/rest/v1/core")
_search = BaseDatabaseServer(name="pdb_search", base_url="https://search.rcsb.org/rcsbsearch/v2")


@mcp.tool()
def pdb_search_gene(gene_name: str, organism: str = "Homo sapiens") -> str:
    """Search PDB for experimental structures of a protein by gene name.
    Returns PDB IDs, resolution, and method.
    Example: 'TP53', 'BRCA1', 'EGFR'."""
    query = {
        "query": {
            "type": "group",
            "logical_operator": "and",
            "nodes": [
                {"type": "terminal", "service": "text",
                 "parameters": {"attribute": "rcsb_entity_source_organism.rcsb_gene_name.value",
                                "value": gene_name, "operator": "exact_match"}},
                {"type": "terminal", "service": "text",
                 "parameters": {"attribute": "rcsb_entity_source_organism.scientific_name",
                                "value": organism, "operator": "exact_match"}},
            ]
        },
        "return_type": "entry",
        "request_options": {"results_content_type": ["experimental"], "paginate": {"start": 0, "rows": 5}},
    }
    try:
        _search._rate_limit()
        with httpx.Client(timeout=30) as client:
            resp = client.post(f"{_search.base_url}/query", json=query)
            resp.raise_for_status()
            result = resp.json()
        total = result.get("total_count", 0)
        ids = [r.get("identifier", "") for r in result.get("result_set", [])]
        return json.dumps({"gene": gene_name, "total_structures": total, "top_pdb_ids": ids})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def pdb_entry(pdb_id: str) -> str:
    """Get details about a PDB structure (resolution, method, title, release date).
    Example: '4HHB' (hemoglobin), '1TSR' (TP53)."""
    try:
        result = _data.get(f"entry/{pdb_id}")
        if isinstance(result, dict):
            cell = result.get("cell", {})
            exptl = result.get("exptl", [{}])[0] if result.get("exptl") else {}
            return json.dumps({
                "pdb_id": pdb_id,
                "title": result.get("struct", {}).get("title", ""),
                "method": exptl.get("method", ""),
                "resolution": result.get("rcsb_entry_info", {}).get("resolution_combined", [None])[0],
                "release_date": result.get("rcsb_accession_info", {}).get("initial_release_date", ""),
                "polymer_entity_count": result.get("rcsb_entry_info", {}).get("polymer_entity_count", 0),
            })
        return _data.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def pdb_search_uniprot(uniprot_id: str) -> str:
    """Search PDB for structures by UniProt accession.
    Example: 'P04637' (TP53), 'P38398' (BRCA1)."""
    query = {
        "query": {
            "type": "terminal", "service": "text",
            "parameters": {"attribute": "rcsb_polymer_entity_container_identifiers.uniprot_ids",
                           "value": uniprot_id, "operator": "exact_match"}
        },
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": 5}},
    }
    try:
        _search._rate_limit()
        with httpx.Client(timeout=30) as client:
            resp = client.post(f"{_search.base_url}/query", json=query)
            resp.raise_for_status()
            result = resp.json()
        total = result.get("total_count", 0)
        ids = [r.get("identifier", "") for r in result.get("result_set", [])]
        return json.dumps({"uniprot_id": uniprot_id, "total_structures": total, "top_pdb_ids": ids})
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
