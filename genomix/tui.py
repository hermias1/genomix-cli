"""Genomix interactive terminal UI — immersive chat experience."""
from __future__ import annotations

import os
import time
import threading
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

from genomix import __version__

STYLE = Style.from_dict({
    "prompt": "#00d787 bold",
    "": "#d0d0d0",
})

BANNER = r"""[bold #00d787]
   ██████╗ ███████╗███╗   ██╗ ██████╗ ███╗   ███╗██╗██╗  ██╗
  ██╔════╝ ██╔════╝████╗  ██║██╔═══██╗████╗ ████║██║╚██╗██╔╝
  ██║  ███╗█████╗  ██╔██╗ ██║██║   ██║██╔████╔██║██║ ╚███╔╝
  ██║   ██║██╔══╝  ██║╚██╗██║██║   ██║██║╚██╔╝██║██║ ██╔██╗
  ╚██████╔╝███████╗██║ ╚████║╚██████╔╝██║ ╚═╝ ██║██║██╔╝ ██╗
   ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═╝[/]
"""

SLASH_COMMANDS = [
    "/qc", "/align", "/variant-call", "/annotate", "/pipeline",
    "/blast", "/msa", "/phylo", "/summary", "/search", "/explain", "/report",
    "/mcp", "/swarm", "/history", "/provider", "/model", "/help", "/quit",
]

COMMAND_SKILL_MAP = {
    "/qc": "sequencing/quality-control",
    "/align": "sequencing/alignment",
    "/variant-call": "sequencing/variant-calling",
    "/annotate": "sequencing/annotation",
    "/blast": "comparative/blast-analysis",
    "/msa": "comparative/multiple-alignment",
    "/phylo": "comparative/phylogenetics",
    "/summary": "exploration/sequence-summary",
    "/search": "exploration/database-search",
    "/explain": "exploration/variant-explain",
    "/report": "reporting/clinical-report",
}

COMMAND_DESCRIPTIONS = {
    "/qc": "Run quality control (FastQC)",
    "/align": "Align reads to reference genome",
    "/variant-call": "Call variants (GATK/FreeBayes)",
    "/annotate": "Annotate variants (SnpEff/VEP)",
    "/pipeline": "Full pipeline: QC → align → call → annotate",
    "/blast": "BLAST similarity search",
    "/msa": "Multiple sequence alignment",
    "/phylo": "Phylogenetic tree construction",
    "/summary": "Summarize a genomic file",
    "/search": "Query databases (NCBI, Ensembl...)",
    "/explain": "Explain a variant, gene, or region",
    "/report": "Generate clinical HTML report from VCF",
    "/mcp": "Manage MCP servers (connect, status)",
    "/swarm": "Show background analyses",
    "/history": "Session history",
    "/provider": "Switch AI provider",
    "/model": "Switch model",
    "/help": "Show available commands",
    "/quit": "Exit genomix",
}


class GenomixTUI:
    """Immersive terminal chat interface for Genomix."""

    def __init__(self):
        self.console = Console()
        self.agent_loop = None
        self.project = None
        self.config = None
        self.mcp_manager = None
        self.tool_registry = None
        self._spinner_active = False

    def _detect_project(self):
        """Try to discover an active genomix project."""
        from genomix.project.manager import ProjectManager, ProjectNotFoundError
        try:
            self.project = ProjectManager.discover(Path.cwd())
        except ProjectNotFoundError:
            self.project = None

    def _load_config(self):
        """Load configuration."""
        from genomix.config import load_config
        self.config = load_config()

    def _ensure_tool_registry(self):
        """Create the shared tool registry with file tools + MCP tools."""
        if self.tool_registry is not None:
            return
        from genomix.tools.registry import ToolRegistry
        from genomix.tools.file_tools import register_file_tools
        self.tool_registry = ToolRegistry()
        register_file_tools(self.tool_registry)

    def _init_mcp(self):
        """Initialize MCP manager and auto-connect available servers."""
        from genomix.tools.mcp_manager import MCPManager
        self.mcp_manager = MCPManager()
        self.mcp_manager.check_availability()

    def _connect_mcp_servers(self):
        """Connect all available MCP servers and register tools."""
        if not self.mcp_manager:
            self._init_mcp()
        self._ensure_tool_registry()

        from genomix.tools.mcp_manager import ServerStatus

        # Connect database servers first (no binaries needed), then biotools
        for server in self.mcp_manager.get_server_list():
            if server.status in (ServerStatus.MISSING_BINARY, ServerStatus.DISABLED):
                continue
            self.console.print(f"  [dim]Connecting to {server.display_name}...[/]", end="")
            success = self.mcp_manager.connect(server.name)
            if success:
                count = self.mcp_manager.register_tools(server.name, self.tool_registry)
                self.console.print(f" [green]✓[/] [dim]({count} tools)[/]")
            else:
                self.console.print(f" [red]✗[/] [dim]{server.error[:60]}[/]")

    def _create_agent_loop(self, skill_path=None, max_iterations=None):
        """Create a wired agent loop with UI callbacks."""
        from genomix.config import load_config, load_secrets
        from genomix.providers import get_provider
        from genomix.runtime import get_skill_dirs, is_local_provider
        from genomix.skills.registry import SkillRegistry
        from genomix.agent.prompt_builder import build_system_prompt
        from genomix.agent.loop import AgentLoop

        self._ensure_tool_registry()

        config = load_config()
        secrets = load_secrets()
        api_key = secrets.get(f"{config.provider}_api_key", secrets.get("anthropic_api_key", ""))
        provider = get_provider(config.provider, api_key=api_key, model=config.model)

        skill_body = None
        if skill_path:
            skills_dirs = get_skill_dirs()
            skill_registry = SkillRegistry(skills_dirs)
            skill = skill_registry.get_skill_by_path(skill_path)
            if skill:
                skill_body = skill.body

        privacy = config.privacy_mode or is_local_provider(config.provider)
        system_prompt = build_system_prompt(
            project=self.project, skill_body=skill_body, privacy_mode=privacy
        )

        return AgentLoop(
            provider=provider,
            tool_registry=self.tool_registry,
            system_prompt=system_prompt,
            max_iterations=max_iterations or 12,
            on_tool_call=self._on_tool_call,
            on_tool_result=self._on_tool_result,
            on_thinking=self._on_thinking,
        )

    def _on_tool_call(self, name: str, args: dict):
        """Called when the agent invokes a tool."""
        args_str = ", ".join(f"{k}={v!r}" for k, v in list(args.items())[:3])
        if len(args_str) > 60:
            args_str = args_str[:57] + "..."
        self.console.print(
            f"  [dim #00d787]⚡ {name}[/]([dim]{args_str}[/])"
        )

    def _on_tool_result(self, name: str, result: str):
        """Called when a tool returns a result."""
        preview = result.replace("\n", " ")[:80]
        self.console.print(f"  [dim]  ↳ {preview}[/]")

    def _on_thinking(self, message: str):
        """Called when the agent starts thinking."""
        pass  # Spinner handles this

    def _print_banner(self):
        """Print the startup banner."""
        self.console.print(BANNER)
        self.console.print(
            f"  [dim]v{__version__}[/] — [bold]AI-powered genome analysis[/]\n"
        )

    def _print_status(self):
        """Print project and provider status."""
        self._detect_project()
        self._load_config()
        self._init_mcp()

        status = Table.grid(padding=(0, 2))
        status.add_column(style="bold #00d787")
        status.add_column()

        if self.project:
            status.add_row("  Project", self.project.name)
            status.add_row("  Organism", self.project.organism)
            status.add_row("  Reference", self.project.reference_genome)
        else:
            status.add_row("  Project", "[dim]None — run /init or genomix init[/]")

        provider_name = self.config.provider if self.config else "claude"
        model_name = self.config.model if self.config else "?"
        privacy = "🔒 ON" if (self.config and (self.config.privacy_mode or self.config.provider == "opencode")) else "OFF"
        status.add_row("  Provider", f"{provider_name} ({model_name})")
        status.add_row("  Privacy", privacy)

        # MCP server summary
        from genomix.tools.mcp_manager import ServerStatus
        available = sum(1 for s in self.mcp_manager.get_server_list() if s.status != ServerStatus.MISSING_BINARY)
        missing = sum(1 for s in self.mcp_manager.get_server_list() if s.status == ServerStatus.MISSING_BINARY)
        total = len(self.mcp_manager.servers)
        mcp_str = f"{available} available"
        if missing:
            mcp_str += f", [dim]{missing} missing binary[/]"
        status.add_row("  MCP Servers", f"{total} registered ({mcp_str})")

        self.console.print(Panel(status, border_style="#333333", padding=(0, 1)))
        self.console.print()

    def _print_help(self):
        """Print formatted help."""
        self.console.print("\n[bold #00d787]  Available Commands[/]\n")

        table = Table(show_header=False, box=None, padding=(0, 2), show_edge=False)
        table.add_column(style="bold cyan", min_width=18)
        table.add_column(style="dim")

        sections = [
            ("Analysis", ["/qc", "/align", "/variant-call", "/annotate", "/pipeline"]),
            ("Comparative", ["/blast", "/msa", "/phylo"]),
            ("Exploration", ["/summary", "/search", "/explain"]),
            ("Reporting", ["/report"]),
            ("Session", ["/mcp", "/swarm", "/history", "/provider", "/model", "/help", "/quit"]),
        ]
        for section_name, cmds in sections:
            table.add_row(f"  [bold dim]{section_name}[/]", "")
            for cmd in cmds:
                table.add_row(f"    {cmd}", COMMAND_DESCRIPTIONS.get(cmd, ""))

        self.console.print(table)
        self.console.print()
        self.console.print("  [dim]Or just type a question in natural language.[/]\n")

    def _run_agent(self, message: str, skill_path: str | None = None):
        """Run the agent and display response with streaming renderer."""
        from genomix.tui_renderer import StreamingRenderer

        try:
            from genomix.runtime import iteration_budget_for

            max_iterations = iteration_budget_for(message, skill_path=skill_path)
            if skill_path or self.agent_loop is None:
                loop = self._create_agent_loop(skill_path=skill_path, max_iterations=max_iterations)
                if not skill_path:
                    self.agent_loop = loop
            else:
                loop = self.agent_loop
                loop.max_iterations = max_iterations

            renderer = StreamingRenderer(self.console)
            renderer.show_thinking()
            start_index = len(loop.messages)
            for event in loop.chat_stream(message):
                renderer.handle_event(event)

            if self.project:
                from genomix.agent.session_store import SessionStore

                title = (message.splitlines()[0][:80] or "Session").strip()
                store = SessionStore(self.project.root / ".genomix" / "runtime" / "sessions.db")
                store.save_session(loop.messages[start_index:], title=title)

        except KeyboardInterrupt:
            self.console.print("\n[dim]Interrupted.[/]\n")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/]\n")

    def _handle_mcp(self, args: str = ""):
        """Handle /mcp command — list, connect, disconnect servers."""
        from genomix.tools.mcp_manager import ServerStatus

        if not self.mcp_manager:
            self._init_mcp()

        parts = args.strip().split(maxsplit=1)
        subcmd = parts[0] if parts else ""
        subcmd_arg = parts[1] if len(parts) > 1 else ""

        if subcmd == "connect":
            if not subcmd_arg:
                # Connect all
                self.console.print("\n[bold #00d787]  Connecting MCP servers...[/]\n")
                self._connect_mcp_servers()
            elif subcmd_arg in self.mcp_manager.servers:
                self._ensure_tool_registry()
                self.console.print(f"\n  Connecting to {subcmd_arg}...", end="")
                success = self.mcp_manager.connect(subcmd_arg)
                if success:
                    count = self.mcp_manager.register_tools(subcmd_arg, self.tool_registry)
                    self.console.print(f" [green]✓[/] ({count} tools)")
                    self.agent_loop = None  # force re-create with new tools
                else:
                    self.console.print(f" [red]✗[/] {self.mcp_manager.servers[subcmd_arg].error[:80]}")
            else:
                self.console.print(f"  [red]Unknown server: {subcmd_arg}[/]")
            self.console.print()
            return

        if subcmd == "disconnect":
            if subcmd_arg in self.mcp_manager.servers:
                self.mcp_manager.disconnect(subcmd_arg)
                self.console.print(f"  Disconnected from {subcmd_arg}.\n")
                self.agent_loop = None
            else:
                self.console.print(f"  [red]Unknown server: {subcmd_arg}[/]\n")
            return

        # Default: show status
        self.console.print("\n[bold #00d787]  MCP Servers[/]\n")

        table = Table(show_header=True, box=None, padding=(0, 2), show_edge=False)
        table.add_column("Server", style="bold")
        table.add_column("Category", style="dim")
        table.add_column("Status")
        table.add_column("Tools", justify="right")
        table.add_column("Description", style="dim")

        status_style = {
            ServerStatus.CONNECTED: "[green]● connected[/]",
            ServerStatus.CONNECTING: "[yellow]◌ connecting[/]",
            ServerStatus.DISCONNECTED: "[dim]○ disconnected[/]",
            ServerStatus.ERROR: "[red]✗ error[/]",
            ServerStatus.DISABLED: "[dim]- disabled[/]",
            ServerStatus.MISSING_BINARY: "[yellow]⚠ missing binary[/]",
        }

        for s in self.mcp_manager.get_server_list():
            status_str = status_style.get(s.status, str(s.status))
            tools_str = str(s.tools_count) if s.tools_count else "-"
            table.add_row(f"  {s.display_name}", s.category, status_str, tools_str, s.description)

        self.console.print(table)
        self.console.print()

        connected = sum(1 for s in self.mcp_manager.servers.values() if s.status == ServerStatus.CONNECTED)
        total_tools = sum(s.tools_count for s in self.mcp_manager.servers.values())
        self.console.print(f"  [dim]{connected} connected, {total_tools} tools available[/]")
        self.console.print(f"  [dim]Usage: /mcp connect [name] | /mcp disconnect <name>[/]\n")

    def _handle_swarm(self):
        """Handle /swarm command."""
        from genomix.swarm.manager import SwarmManager
        if not self.project:
            self.console.print("[dim]No project found.[/]")
            return
        sm = SwarmManager(state_dir=self.project.root / ".genomix" / "runtime" / "swarm")
        tasks = sm.list_tasks()
        if not tasks:
            self.console.print("[dim]  No background analyses running.[/]")
        else:
            table = Table(show_header=True, box=None, padding=(0, 1))
            table.add_column("ID", style="bold")
            table.add_column("Command", style="cyan")
            table.add_column("Status")
            for t in tasks:
                color = {"running": "yellow", "completed": "green", "failed": "red"}.get(t.status.value, "dim")
                table.add_row(f"#{t.id}", t.command, f"[{color}]{t.status.value}[/]")
            self.console.print(table)
        self.console.print()

    def _handle_history(self, query: str = ""):
        """Handle /history command."""
        from genomix.agent.session_store import SessionStore
        if not self.project:
            self.console.print("[dim]No project found.[/]")
            return
        store = SessionStore(self.project.root / ".genomix" / "runtime" / "sessions.db")
        if query:
            results = store.search(query)
            for r in results:
                self.console.print(f"  [bold]{r['id']}[/]  {r['title']}")
        else:
            sessions = store.list_sessions()
            if not sessions:
                self.console.print("[dim]  No session history yet.[/]")
            else:
                for s in sessions:
                    self.console.print(f"  [bold]{s['id']}[/]  {s['title']}  [dim]{s['created_at']}[/]")
        self.console.print()

    def _handle_report(self, args: str):
        """Generate a clinical HTML report from a VCF file."""
        import json as json_mod
        from genomix.report import generate_report, save_report

        parts = args.split()
        vcf_path = parts[0]
        output_path = None
        if "--output" in parts:
            idx = parts.index("--output")
            if idx + 1 < len(parts):
                output_path = Path(parts[idx + 1])

        if not Path(vcf_path).exists():
            self.console.print(f"[red]  File not found: {vcf_path}[/]\n")
            return

        self.console.print(f"\n[bold #00d787]  Generating clinical report for {vcf_path}...[/]\n")

        # Use agent with clinical-report skill to analyze
        # Use streaming with a spinner so user sees progress
        from genomix.tui_renderer import StreamingRenderer
        from genomix.providers.base import TextDelta, StreamDone

        loop = self._create_agent_loop(skill_path="reporting/clinical-report", max_iterations=6)
        prompt = (
            f"Read the file {vcf_path} and list all variants as a JSON array. "
            f"Respond ONLY with a JSON array like: "
            f'[{{"gene":"BRCA1","variant":"chr17:43094464 G>A","type":"missense","zygosity":"Heterozygous","significance":"Pathogenic"}},...] '
            f"Nothing else — just the JSON array."
        )

        # Stream with spinner, accumulate full text
        renderer = StreamingRenderer(self.console)
        renderer.show_thinking()
        response = ""
        for event in loop.chat_stream(prompt):
            if isinstance(event, TextDelta):
                response += event.text
            renderer.handle_event(event)

        # Try to parse JSON from response
        try:
            # Find JSON array in response
            arr_start = response.find("[")
            arr_end = response.rfind("]") + 1
            if arr_start == -1:
                raise ValueError("No JSON array found in response")
            variants = json_mod.loads(response[arr_start:arr_end])

            # Generate interpretation and recommendations from variant data
            interpretation = self._generate_interpretation(variants)
            recommendations = self._generate_recommendations(variants)

            # Determine reference from project
            reference = "GRCh38"
            if self.project:
                reference = self.project.reference_genome

            html = generate_report(
                filename=vcf_path,
                variants=variants,
                interpretation=interpretation,
                recommendations=recommendations,
                reference=reference,
            )

            # Save
            if output_path is None:
                stem = Path(vcf_path).stem
                if self.project:
                    output_path = self.project.root / "reports" / f"{stem}_report.html"
                else:
                    output_path = Path(f"{stem}_report.html")

            saved = save_report(html, output_path)
            self.console.print(f"[green]  ✓ Report saved to {saved}[/]")
            self.console.print(f"[dim]    Open with: open {saved}[/]\n")

            # Show summary
            self.console.print(f"  [bold]{len(variants)} variants[/] analyzed\n")
            for v in variants:
                sig = v.get("significance", "?")
                color = {"Pathogenic": "red", "Likely_pathogenic": "yellow", "Risk_factor": "magenta"}.get(sig, "dim")
                self.console.print(f"    [{color}]●[/] {v.get('gene', '?')} — {v.get('variant', '')} — {sig}")
            self.console.print()

        except (json_mod.JSONDecodeError, ValueError) as e:
            self.console.print(f"[yellow]  Could not generate structured report. Showing raw analysis:[/]\n")
            from rich.markdown import Markdown
            self.console.print(Markdown(response))
            self.console.print()

    @staticmethod
    def _generate_interpretation(variants: list[dict]) -> str:
        """Auto-generate clinical interpretation HTML from variant list."""
        lines = []
        pathogenic = [v for v in variants if "pathogenic" in v.get("significance", "").lower()]
        risk = [v for v in variants if "risk" in v.get("significance", "").lower()]

        if pathogenic:
            genes = ", ".join(set(v.get("gene", "?") for v in pathogenic))
            lines.append(f"<p><strong>{len(pathogenic)} pathogenic variant(s)</strong> identified in: {genes}.</p>")
            for v in pathogenic:
                gene = v.get("gene", "?")
                vtype = v.get("type", "variant").replace("_", " ")
                zyg = v.get("zygosity", "").lower()
                lines.append(f"<p><strong>{gene}</strong> — {vtype} ({zyg}). "
                           f"This variant is classified as <strong>{v.get('significance', '?')}</strong> "
                           f"and may have significant clinical implications.</p>")

        if risk:
            for v in risk:
                lines.append(f"<p><strong>{v.get('gene', '?')}</strong> — {v.get('type', 'variant').replace('_', ' ')} "
                           f"identified as a <strong>risk factor</strong>. "
                           f"This does not guarantee disease but increases susceptibility.</p>")

        carrier = [v for v in variants if v.get("zygosity", "").lower() == "heterozygous"
                   and v.get("significance", "").lower() == "pathogenic"
                   and v.get("gene", "") in ("CFTR", "HBB", "SMN1")]
        if carrier:
            genes = ", ".join(v.get("gene", "?") for v in carrier)
            lines.append(f"<p><strong>Carrier status:</strong> Heterozygous carrier for recessive condition(s) "
                        f"in {genes}. The individual is likely unaffected but can transmit the variant.</p>")

        return "\n".join(lines) if lines else "<p>No significant clinical findings.</p>"

    @staticmethod
    def _generate_recommendations(variants: list[dict]) -> str:
        """Auto-generate clinical recommendations HTML from variant list."""
        recs = []
        genes = [v.get("gene", "") for v in variants if "pathogenic" in v.get("significance", "").lower()]

        if any(g in ("BRCA1", "BRCA2") for g in genes):
            recs.append("<div class='recommendation'><strong>Hereditary Cancer Syndrome:</strong> "
                       "Pathogenic BRCA1/BRCA2 variants detected. Recommend genetic counseling, "
                       "enhanced cancer surveillance (mammography, MRI), and evaluation of "
                       "risk-reducing options. Family members should be offered cascade testing.</div>")

        if "CFTR" in genes:
            recs.append("<div class='recommendation'><strong>Cystic Fibrosis:</strong> "
                       "CFTR variant detected. Carrier testing recommended for reproductive partner. "
                       "Genetic counseling advised for family planning.</div>")

        if "HBB" in genes:
            recs.append("<div class='recommendation'><strong>Hemoglobinopathy:</strong> "
                       "HBB variant detected (sickle cell trait). Carrier testing recommended for "
                       "reproductive partner. Genetic counseling advised.</div>")

        if any(v.get("gene") == "APOE" for v in variants):
            recs.append("<div class='recommendation'><strong>Alzheimer's Risk:</strong> "
                       "APOE risk variant identified. This is a susceptibility factor, not diagnostic. "
                       "No specific clinical action required but may inform personal health planning.</div>")

        if not recs:
            recs.append("<div class='recommendation'>No specific clinical recommendations based on the "
                       "identified variants. Standard of care applies.</div>")

        recs.append("<div class='recommendation'><strong>General:</strong> "
                   "This report is for research/informational purposes. Clinical decisions should "
                   "involve a qualified genetic counselor or medical geneticist.</div>")

        return "\n".join(recs)

    def run(self):
        """Main interactive loop."""
        # Suppress noisy logs from MCP/httpx during interactive use
        import logging
        logging.getLogger("mcp").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)

        self._print_banner()
        self._print_status()

        # Auto-connect MCP servers
        self.console.print("[bold #00d787]  Connecting MCP servers...[/]\n")
        self._connect_mcp_servers()
        self.console.print()

        completer = WordCompleter(SLASH_COMMANDS, sentence=True)
        session = PromptSession(
            style=STYLE,
            completer=completer,
        )

        while True:
            try:
                user_input = session.prompt(
                    HTML("<prompt>❯ </prompt>"),
                ).strip()
            except (EOFError, KeyboardInterrupt):
                self.console.print("\n[dim]Goodbye! 🧬[/]\n")
                break

            if not user_input:
                continue

            if user_input in ("/quit", "/exit", "/q"):
                self.console.print("[dim]Goodbye! 🧬[/]\n")
                break

            if user_input == "/help":
                self._print_help()
                continue

            parts = user_input.split(maxsplit=1)
            cmd = parts[0]
            cmd_args = parts[1] if len(parts) > 1 else ""

            # Session commands
            if cmd == "/mcp":
                self._handle_mcp(cmd_args)
                continue
            if cmd == "/swarm":
                self._handle_swarm()
                continue
            if cmd == "/history":
                self._handle_history(cmd_args)
                continue
            if cmd == "/provider":
                if cmd_args:
                    from genomix.config import load_config, save_config
                    from genomix.providers import SUPPORTED_PROVIDERS

                    if cmd_args not in SUPPORTED_PROVIDERS:
                        self.console.print(f"[red]  Unknown provider: {cmd_args}[/]\n")
                        continue
                    config = load_config()
                    config.provider = cmd_args
                    save_config(config)
                    self.config = config
                    self.console.print(f"[#00d787]  Switched to provider: {cmd_args}[/]\n")
                    self.agent_loop = None
                else:
                    self._load_config()
                    self.console.print(f"  Provider: [bold]{self.config.provider}[/]\n")
                continue
            if cmd == "/model":
                if cmd_args:
                    from genomix.config import load_config, save_config

                    config = load_config()
                    config.model = cmd_args
                    save_config(config)
                    self.config = config
                    self.console.print(f"[#00d787]  Switched to model: {cmd_args}[/]\n")
                    self.agent_loop = None
                else:
                    self._load_config()
                    self.console.print(f"  Model: [bold]{self.config.model}[/]\n")
                continue

            if cmd == "/report":
                if not cmd_args:
                    self.console.print("[dim]  Usage: /report <vcf_file> [--output path.html][/]\n")
                    continue
                self._handle_report(cmd_args)
                continue

            # Skill-mapped slash commands
            if cmd in COMMAND_SKILL_MAP:
                self.console.print()
                self._run_agent(f"{cmd} {cmd_args}".strip(), skill_path=COMMAND_SKILL_MAP[cmd])
                continue

            # Natural language
            self.console.print()
            self._run_agent(user_input)
