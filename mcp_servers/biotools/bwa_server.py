"""BWA-MEM2 MCP server for read alignment."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_biotool import BaseBiotoolServer

mcp = FastMCP("bwa")
_bwa = BaseBiotoolServer("bwa-mem2")


@mcp.tool()
def bwa_index(ref: str) -> str:
    """Index a reference genome with bwa-mem2."""
    if not _bwa.check_binary():
        import json
        return json.dumps({"error": "bwa-mem2 not found. Run 'genomix setup'."})
    return _bwa.run_command(["index", ref])


@mcp.tool()
def bwa_mem(ref: str, read1: str, read2: str = "", threads: int = 4, output_sam: str = "output.sam") -> str:
    """Align reads to a reference genome using bwa-mem2."""
    if not _bwa.check_binary():
        import json
        return json.dumps({"error": "bwa-mem2 not found. Run 'genomix setup'."})
    args = ["mem", "-t", str(threads), ref, read1]
    if read2:
        args.append(read2)
    args += ["-o", output_sam]
    return _bwa.run_command(args)


if __name__ == "__main__":
    mcp.run()
