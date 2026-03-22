"""gnomAD MCP server — population allele frequencies."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer
import httpx

mcp = FastMCP("gnomad")
_server = BaseDatabaseServer(name="gnomad", base_url="https://gnomad.broadinstitute.org/api")


@mcp.tool()
def gnomad_variant(variant_id: str, dataset: str = "gnomad_r4") -> str:
    """Get population allele frequencies for a variant from gnomAD.
    variant_id format: '1-55516888-G-A' (chrom-pos-ref-alt) or rsID like 'rs123'.
    Returns frequencies across populations (AFR, AMR, ASJ, EAS, FIN, NFE, SAS, etc.)."""
    query = '''
    query($variantId: String!, $dataset: DatasetId!) {
      variant(variantId: $variantId, dataset: $dataset) {
        variant_id
        rsids
        genome {
          ac
          an
          af
          populations {
            id
            ac
            an
            af
          }
        }
        exome {
          ac
          an
          af
          populations {
            id
            ac
            an
            af
          }
        }
      }
    }
    '''
    try:
        _server._rate_limit()
        with httpx.Client(timeout=30) as client:
            resp = client.post(_server.base_url, json={
                "query": query,
                "variables": {"variantId": variant_id, "dataset": dataset}
            })
            resp.raise_for_status()
            result = resp.json()
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def gnomad_gene(gene_symbol: str, dataset: str = "gnomad_r4") -> str:
    """Get gene constraint metrics from gnomAD (pLI, LOEUF, missense Z-score).
    Useful for assessing gene tolerance to loss-of-function variants."""
    query = '''
    query($gene: String!, $dataset: DatasetId!) {
      gene(gene_symbol: $gene, reference_genome: GRCh38) {
        symbol
        gene_id
        gnomad_constraint {
          pli
          loeuf
          mis_z
          syn_z
        }
      }
    }
    '''
    try:
        _server._rate_limit()
        with httpx.Client(timeout=30) as client:
            resp = client.post(_server.base_url, json={
                "query": query,
                "variables": {"gene": gene_symbol, "dataset": dataset}
            })
            resp.raise_for_status()
            result = resp.json()
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
