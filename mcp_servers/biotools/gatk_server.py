"""GATK MCP server for variant calling and read processing."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mcp.server.fastmcp import FastMCP
from mcp_servers.base_biotool import BaseBiotoolServer

mcp = FastMCP("gatk")
_gatk = BaseBiotoolServer("gatk")


@mcp.tool()
def gatk_haplotype_caller(bam: str, ref: str, output_vcf: str, intervals: str = "") -> str:
    """Call germline SNPs and indels using GATK HaplotypeCaller."""
    if not _gatk.check_binary():
        import json
        return json.dumps({"error": "gatk not found. Run 'genomix setup'."})
    args = ["HaplotypeCaller", "-I", bam, "-R", ref, "-O", output_vcf]
    if intervals:
        args += ["-L", intervals]
    return _gatk.run_command(args)


@mcp.tool()
def gatk_mark_duplicates(bam: str, output_bam: str, metrics: str = "dup_metrics.txt") -> str:
    """Mark duplicate reads in a BAM file using GATK MarkDuplicates."""
    if not _gatk.check_binary():
        import json
        return json.dumps({"error": "gatk not found. Run 'genomix setup'."})
    args = ["MarkDuplicates", "-I", bam, "-O", output_bam, "-M", metrics]
    return _gatk.run_command(args)


@mcp.tool()
def gatk_base_recalibrator(bam: str, ref: str, known_sites: str, output_table: str = "recal_data.table") -> str:
    """Generate base quality score recalibration table using GATK BaseRecalibrator."""
    if not _gatk.check_binary():
        import json
        return json.dumps({"error": "gatk not found. Run 'genomix setup'."})
    args = ["BaseRecalibrator", "-I", bam, "-R", ref, "--known-sites", known_sites, "-O", output_table]
    return _gatk.run_command(args)


if __name__ == "__main__":
    mcp.run()
