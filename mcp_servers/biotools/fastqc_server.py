"""FastQC MCP server for sequencing quality control."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_biotool import BaseBiotoolServer

mcp = FastMCP("fastqc")
_fastqc = BaseBiotoolServer("fastqc")


@mcp.tool()
def fastqc_analyze(input_files: str, output_dir: str = ".", threads: int = 2) -> str:
    """Run FastQC quality analysis on one or more FASTQ/BAM/SAM files.

    input_files: space-separated list of input files or a single file path.
    """
    if not _fastqc.check_binary():
        import json
        return json.dumps({"error": "fastqc not found. Run 'genomix setup'."})
    files = input_files.split()
    args = ["--outdir", output_dir, "--threads", str(threads)] + files
    return _fastqc.run_command(args)


if __name__ == "__main__":
    mcp.run()
