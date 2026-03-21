"""Samtools MCP server for BAM/SAM file processing."""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_biotool import BaseBiotoolServer

mcp = FastMCP("samtools")
_server = BaseBiotoolServer("samtools")


@mcp.tool()
def samtools_stats(bam: str) -> str:
    """Generate statistics for a BAM/SAM file."""
    if not _server.check_binary():
        return json.dumps({"error": "samtools not found. Run 'genomix setup'."})
    return _server.run_command(["stats", bam])


@mcp.tool()
def samtools_flagstat(bam: str) -> str:
    """Report alignment statistics from a BAM/SAM file."""
    if not _server.check_binary():
        return json.dumps({"error": "samtools not found. Run 'genomix setup'."})
    return _server.run_command(["flagstat", bam])


@mcp.tool()
def samtools_view(bam: str, output: str, region: str = "", flags: str = "") -> str:
    """View and filter BAM/SAM/CRAM files."""
    if not _server.check_binary():
        return json.dumps({"error": "samtools not found. Run 'genomix setup'."})
    args = ["view", "-o", output]
    if flags:
        args += flags.split()
    args.append(bam)
    if region:
        args.append(region)
    return _server.run_command(args)


@mcp.tool()
def samtools_sort(bam: str, output: str, threads: int = 4) -> str:
    """Sort a BAM file by coordinates."""
    if not _server.check_binary():
        return json.dumps({"error": "samtools not found. Run 'genomix setup'."})
    return _server.run_command(["sort", "-@", str(threads), "-o", output, bam])


@mcp.tool()
def samtools_index(bam: str) -> str:
    """Index a sorted BAM file."""
    if not _server.check_binary():
        return json.dumps({"error": "samtools not found. Run 'genomix setup'."})
    return _server.run_command(["index", bam])


@mcp.tool()
def samtools_depth(bam: str, region: str = "", min_base_quality: int = 0) -> str:
    """Compute per-base read depth for a BAM file."""
    if not _server.check_binary():
        return json.dumps({"error": "samtools not found. Run 'genomix setup'."})
    args = ["depth"]
    if min_base_quality > 0:
        args += ["-q", str(min_base_quality)]
    if region:
        args += ["-r", region]
    args.append(bam)
    return _server.run_command(args)


if __name__ == "__main__":
    mcp.run()
