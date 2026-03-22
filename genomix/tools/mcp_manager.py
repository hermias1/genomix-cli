"""MCP server lifecycle manager — discover, connect, and manage MCP servers."""
from __future__ import annotations

import asyncio
import json
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from genomix.tools.registry import ToolRegistry


class ServerStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"
    MISSING_BINARY = "missing_binary"


@dataclass
class MCPServerInfo:
    """Info about an MCP server."""
    name: str
    display_name: str
    category: str  # "biotools" or "databases"
    description: str
    status: ServerStatus = ServerStatus.DISCONNECTED
    tools_count: int = 0
    tool_names: list[str] = field(default_factory=list)
    error: str = ""
    binary: str = ""  # for biotools — the required binary name
    module: str = ""  # Python module path for the server


# Built-in MCP server registry
BUILTIN_SERVERS: list[MCPServerInfo] = [
    # Biotools
    MCPServerInfo(name="samtools", display_name="SAMtools", category="biotools",
                  description="BAM/SAM manipulation (view, sort, index, stats)",
                  binary="samtools", module="mcp_servers.biotools.samtools_server"),
    MCPServerInfo(name="bwa", display_name="BWA-MEM2", category="biotools",
                  description="Read alignment to reference genome",
                  binary="bwa-mem2", module="mcp_servers.biotools.bwa_server"),
    MCPServerInfo(name="gatk", display_name="GATK", category="biotools",
                  description="Variant calling (HaplotypeCaller, MarkDuplicates)",
                  binary="gatk", module="mcp_servers.biotools.gatk_server"),
    MCPServerInfo(name="blast", display_name="BLAST+", category="biotools",
                  description="Sequence similarity search (blastn, blastp, blastx)",
                  binary="blastn", module="mcp_servers.biotools.blast_server"),
    MCPServerInfo(name="fastqc", display_name="FastQC", category="biotools",
                  description="Sequencing quality control",
                  binary="fastqc", module="mcp_servers.biotools.fastqc_server"),
    # Databases
    MCPServerInfo(name="ncbi", display_name="NCBI", category="databases",
                  description="Entrez search, fetch, gene info (GenBank, RefSeq)",
                  module="mcp_servers.databases.ncbi_server"),
    MCPServerInfo(name="ensembl", display_name="Ensembl", category="databases",
                  description="Genome browser, VEP, variant info",
                  module="mcp_servers.databases.ensembl_server"),
    MCPServerInfo(name="clinvar", display_name="ClinVar", category="databases",
                  description="Clinical variant significance",
                  module="mcp_servers.databases.clinvar_server"),
    MCPServerInfo(name="dbsnp", display_name="dbSNP", category="databases",
                  description="Known variant catalog",
                  module="mcp_servers.databases.dbsnp_server"),
    MCPServerInfo(name="gnomad", display_name="gnomAD", category="databases",
                  description="Population allele frequencies and gene constraint metrics",
                  module="mcp_servers.databases.gnomad_server"),
    MCPServerInfo(name="omim", display_name="OMIM", category="databases",
                  description="Genetic diseases, gene-phenotype relationships",
                  module="mcp_servers.databases.omim_server"),
    MCPServerInfo(name="pharmgkb", display_name="PharmGKB", category="databases",
                  description="Pharmacogenomics, drug-gene interactions, dosing guidelines",
                  module="mcp_servers.databases.pharmgkb_server"),
    MCPServerInfo(name="cosmic", display_name="COSMIC", category="databases",
                  description="Somatic cancer mutations and cancer gene associations",
                  module="mcp_servers.databases.cosmic_server"),
    MCPServerInfo(name="interpro", display_name="InterPro", category="databases",
                  description="Protein domains, families, functional annotations",
                  module="mcp_servers.databases.interpro_server"),
    MCPServerInfo(name="pubmed", display_name="PubMed", category="databases",
                  description="Biomedical literature search and abstracts",
                  module="mcp_servers.databases.pubmed_server"),
]


class MCPManager:
    """Manages MCP server lifecycle — discovery, connection, tool registration."""

    def __init__(self):
        self.servers: dict[str, MCPServerInfo] = {}
        self._sessions: dict[str, Any] = {}
        self._exit_stacks: dict[str, Any] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

        # Register all built-in servers
        for s in BUILTIN_SERVERS:
            self.servers[s.name] = MCPServerInfo(
                name=s.name, display_name=s.display_name, category=s.category,
                description=s.description, binary=s.binary, module=s.module,
            )

    def check_availability(self) -> None:
        """Check which biotools have their binaries available."""
        for server in self.servers.values():
            if server.category == "biotools" and server.binary:
                if not shutil.which(server.binary):
                    server.status = ServerStatus.MISSING_BINARY

    def get_server_list(self) -> list[MCPServerInfo]:
        """Return all servers sorted by category then name."""
        return sorted(self.servers.values(), key=lambda s: (s.category, s.name))

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop."""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop

    def connect(self, name: str) -> bool:
        """Connect to an MCP server synchronously. Returns True on success."""
        server = self.servers.get(name)
        if not server:
            return False
        if server.status == ServerStatus.MISSING_BINARY:
            server.error = f"Binary '{server.binary}' not found. Run 'genomix setup'."
            server.status = ServerStatus.ERROR
            return False

        server.status = ServerStatus.CONNECTING
        try:
            loop = self._get_loop()
            loop.run_until_complete(self._async_connect(name))
            server.status = ServerStatus.CONNECTED
            return True
        except Exception as e:
            server.status = ServerStatus.ERROR
            server.error = str(e)[:200]
            return False

    def _get_project_root(self) -> str:
        """Find the genomix project root (where mcp_servers/ lives)."""
        # Walk up from this file to find the repo root
        current = Path(__file__).resolve().parent  # genomix/tools/
        for _ in range(5):
            current = current.parent
            if (current / "mcp_servers").is_dir():
                return str(current)
        # Fallback: check PYTHONPATH
        import os
        for p in os.environ.get("PYTHONPATH", "").split(os.pathsep):
            if p and (Path(p) / "mcp_servers").is_dir():
                return p
        return ""

    async def _async_connect(self, name: str) -> None:
        """Connect to an MCP server and cache the session."""
        from contextlib import AsyncExitStack
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client
        import os

        server = self.servers[name]
        # Build env with project root in PYTHONPATH so subprocess finds mcp_servers
        project_root = self._get_project_root()
        env = dict(os.environ)
        # Always inject the project root — critical for editable installs
        # where the main process uses .pth but subprocesses don't
        paths = []
        if project_root:
            paths.append(project_root)
        existing = env.get("PYTHONPATH", "")
        if existing:
            paths.append(existing)
        # Also add sys.path entries that might contain mcp_servers
        for p in sys.path:
            if p and (Path(p) / "mcp_servers").is_dir() and p not in paths:
                paths.append(p)
        env["PYTHONPATH"] = os.pathsep.join(paths)
        # Suppress noisy logging in MCP server subprocesses
        env["GENOMIX_QUIET"] = "1"

        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", server.module],
            env=env,
        )

        stack = AsyncExitStack()
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        # Get tool list
        result = await session.list_tools()
        server.tools_count = len(result.tools)
        server.tool_names = [t.name for t in result.tools]

        self._sessions[name] = session
        self._exit_stacks[name] = stack

    def register_tools(self, name: str, registry: ToolRegistry) -> int:
        """Register a connected server's tools into the ToolRegistry. Returns tool count."""
        server = self.servers.get(name)
        if not server or server.status != ServerStatus.CONNECTED:
            return 0
        if name not in self._sessions:
            return 0

        loop = self._get_loop()
        count = loop.run_until_complete(self._async_register_tools(name, registry))
        return count

    async def _async_register_tools(self, name: str, registry: ToolRegistry) -> int:
        """Register MCP tools into the tool registry."""
        session = self._sessions[name]
        result = await session.list_tools()
        count = 0
        for tool in result.tools:
            def make_handler(server_name: str, tool_name: str):
                def handler(args: dict[str, Any]) -> str:
                    loop = self._get_loop()
                    try:
                        call_result = loop.run_until_complete(
                            self._sessions[server_name].call_tool(tool_name, args)
                        )
                        # Extract text from MCP result
                        if hasattr(call_result, 'content') and call_result.content:
                            parts = []
                            for block in call_result.content:
                                if hasattr(block, 'text'):
                                    parts.append(block.text)
                            return "\n".join(parts) if parts else str(call_result)
                        return str(call_result)
                    except Exception as e:
                        return json.dumps({"error": str(e)})
                return handler

            schema = tool.inputSchema
            if not isinstance(schema, dict):
                schema = schema.model_dump() if hasattr(schema, 'model_dump') else {"type": "object", "properties": {}}

            registry.register(
                name=tool.name,
                description=tool.description or "",
                parameters=schema,
                handler=make_handler(name, tool.name),
            )
            count += 1
        return count

    def connect_all_available(self, registry: ToolRegistry, on_status=None) -> dict[str, bool]:
        """Connect all available servers and register their tools. Returns {name: success}."""
        self.check_availability()
        results = {}
        for name, server in self.servers.items():
            if server.status == ServerStatus.MISSING_BINARY:
                results[name] = False
                continue
            if on_status:
                on_status(name, "connecting")
            success = self.connect(name)
            if success:
                self.register_tools(name, registry)
                if on_status:
                    on_status(name, "connected", server.tools_count)
            else:
                if on_status:
                    on_status(name, "error", server.error)
            results[name] = success
        return results

    def disconnect(self, name: str) -> None:
        """Disconnect a server."""
        if name in self._exit_stacks:
            try:
                loop = self._get_loop()
                loop.run_until_complete(self._exit_stacks[name].aclose())
            except Exception:
                pass
            del self._exit_stacks[name]
        if name in self._sessions:
            del self._sessions[name]
        if name in self.servers:
            self.servers[name].status = ServerStatus.DISCONNECTED
            self.servers[name].tools_count = 0
            self.servers[name].tool_names = []

    def shutdown(self) -> None:
        """Disconnect all servers."""
        for name in list(self._sessions.keys()):
            self.disconnect(name)
        if self._loop and not self._loop.is_closed():
            self._loop.close()
