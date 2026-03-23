"""AlphaFold Protein Structure Database MCP server."""
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_database import BaseDatabaseServer

mcp = FastMCP("alphafold")
_server = BaseDatabaseServer(name="alphafold", base_url="https://alphafold.ebi.ac.uk/api")


@mcp.tool()
def alphafold_prediction(uniprot_id: str) -> str:
    """Get AlphaFold structure prediction for a protein by UniProt accession.
    Returns confidence scores (pLDDT), structure file URLs, and metadata.
    Example: 'P38398' (BRCA1), 'P04637' (TP53), 'P00533' (EGFR)."""
    try:
        result = _server.get(f"prediction/{uniprot_id}")
        if isinstance(result, list) and result:
            # Extract key info from first prediction
            pred = result[0]
            summary = {
                "uniprot_id": pred.get("uniprotAccession", ""),
                "gene": pred.get("gene", ""),
                "organism": pred.get("organismScientificName", ""),
                "description": pred.get("uniprotDescription", ""),
                "sequence_length": pred.get("sequenceLength", 0),
                "confidence_global": pred.get("globalMetricValue", 0),
                "confidence_very_high": pred.get("fractionPlddtVeryHigh", 0),
                "confidence_confident": pred.get("fractionPlddtConfident", 0),
                "confidence_low": pred.get("fractionPlddtLow", 0),
                "confidence_very_low": pred.get("fractionPlddtVeryLow", 0),
                "pdb_url": pred.get("pdbUrl", ""),
                "cif_url": pred.get("cifUrl", ""),
                "pae_image_url": pred.get("paeImageUrl", ""),
                "model_version": pred.get("latestVersion", ""),
                "created_date": pred.get("modelCreatedDate", ""),
            }
            return json.dumps(summary)
        return _server.compact_json(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def alphafold_confidence(uniprot_id: str) -> str:
    """Get AlphaFold prediction confidence summary for a protein.
    Returns pLDDT score breakdown: very high (>90), confident (70-90), low (50-70), very low (<50).
    Higher pLDDT = more reliable structure prediction."""
    try:
        result = _server.get(f"prediction/{uniprot_id}")
        if isinstance(result, list) and result:
            pred = result[0]
            return json.dumps({
                "gene": pred.get("gene", ""),
                "protein": pred.get("uniprotDescription", ""),
                "global_plddt": pred.get("globalMetricValue", 0),
                "very_high_confidence_pct": round(pred.get("fractionPlddtVeryHigh", 0) * 100, 1),
                "confident_pct": round(pred.get("fractionPlddtConfident", 0) * 100, 1),
                "low_confidence_pct": round(pred.get("fractionPlddtLow", 0) * 100, 1),
                "very_low_confidence_pct": round(pred.get("fractionPlddtVeryLow", 0) * 100, 1),
            })
        return json.dumps({"error": "No prediction found"})
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
