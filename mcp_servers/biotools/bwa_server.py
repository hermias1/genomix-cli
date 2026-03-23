"""BWA MCP server for read alignment."""
import json
import shutil
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_biotool import BaseBiotoolServer

mcp = FastMCP("bwa")

# Prefer bwa-mem2 if available, fall back to bwa
_binary = "bwa-mem2" if shutil.which("bwa-mem2") else "bwa"
_bwa = BaseBiotoolServer(_binary)


@mcp.tool()
def bwa_index(ref: str) -> str:
    """Index a reference genome for alignment."""
    if not _bwa.check_binary():
        return json.dumps({"error": f"{_binary} not found. Run 'genomix setup'."})
    return _bwa.run_command(["index", ref])


@mcp.tool()
def bwa_mem(ref: str, read1: str, read2: str = "", threads: int = 4, output_sam: str = "output.sam") -> str:
    """Align reads to a reference genome using BWA-MEM."""
    if not _bwa.check_binary():
        return json.dumps({"error": f"{_binary} not found. Run 'genomix setup'."})
    args = ["mem", "-t", str(threads), ref, read1]
    if read2:
        args.append(read2)
    args += ["-o", output_sam]
    return _bwa.run_command(args)


if __name__ == "__main__":
    mcp.run()
