"""BLAST MCP server for sequence similarity searching."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_biotool import BaseBiotoolServer

mcp = FastMCP("blast")
_blastn = BaseBiotoolServer("blastn")
_blastp = BaseBiotoolServer("blastp")
_blastx = BaseBiotoolServer("blastx")
_tblastn = BaseBiotoolServer("tblastn")
_makeblastdb = BaseBiotoolServer("makeblastdb")


@mcp.tool()
def blastn(query: str, db: str, output: str = "blastn_out.txt", evalue: float = 1e-5, outfmt: int = 6) -> str:
    """Run nucleotide BLAST search (blastn) against a nucleotide database."""
    if not _blastn.check_binary():
        import json
        return json.dumps({"error": "blastn not found. Run 'genomix setup'."})
    args = ["-query", query, "-db", db, "-out", output, "-evalue", str(evalue), "-outfmt", str(outfmt)]
    return _blastn.run_command(args)


@mcp.tool()
def blastp(query: str, db: str, output: str = "blastp_out.txt", evalue: float = 1e-5, outfmt: int = 6) -> str:
    """Run protein BLAST search (blastp) against a protein database."""
    if not _blastp.check_binary():
        import json
        return json.dumps({"error": "blastp not found. Run 'genomix setup'."})
    args = ["-query", query, "-db", db, "-out", output, "-evalue", str(evalue), "-outfmt", str(outfmt)]
    return _blastp.run_command(args)


@mcp.tool()
def blastx(query: str, db: str, output: str = "blastx_out.txt", evalue: float = 1e-5, outfmt: int = 6) -> str:
    """Run translated nucleotide BLAST search (blastx) against a protein database."""
    if not _blastx.check_binary():
        import json
        return json.dumps({"error": "blastx not found. Run 'genomix setup'."})
    args = ["-query", query, "-db", db, "-out", output, "-evalue", str(evalue), "-outfmt", str(outfmt)]
    return _blastx.run_command(args)


@mcp.tool()
def tblastn(query: str, db: str, output: str = "tblastn_out.txt", evalue: float = 1e-5, outfmt: int = 6) -> str:
    """Run protein query against translated nucleotide database (tblastn)."""
    if not _tblastn.check_binary():
        import json
        return json.dumps({"error": "tblastn not found. Run 'genomix setup'."})
    args = ["-query", query, "-db", db, "-out", output, "-evalue", str(evalue), "-outfmt", str(outfmt)]
    return _tblastn.run_command(args)


@mcp.tool()
def makeblastdb(input_fasta: str, dbtype: str = "nucl") -> str:
    """Create a BLAST database from a FASTA file."""
    if not _makeblastdb.check_binary():
        import json
        return json.dumps({"error": "makeblastdb not found. Run 'genomix setup'."})
    args = ["-in", input_fasta, "-dbtype", dbtype]
    return _makeblastdb.run_command(args)


if __name__ == "__main__":
    mcp.run()
