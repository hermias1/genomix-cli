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
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text
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
    "/blast", "/msa", "/phylo", "/summary", "/search", "/explain",
    "/swarm", "/history", "/provider", "/model", "/help", "/quit",
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

    def _create_agent_loop(self, skill_path=None):
        """Create a wired agent loop with UI callbacks."""
        from genomix.config import load_config, load_secrets
        from genomix.providers import get_provider
        from genomix.tools.registry import ToolRegistry
        from genomix.tools.file_tools import register_file_tools
        from genomix.skills.registry import SkillRegistry
        from genomix.agent.prompt_builder import build_system_prompt
        from genomix.agent.loop import AgentLoop

        config = load_config()
        secrets = load_secrets()
        api_key = secrets.get(f"{config.provider}_api_key", secrets.get("anthropic_api_key", ""))
        provider = get_provider(config.provider, api_key=api_key, model=config.model)

        registry = ToolRegistry()
        register_file_tools(registry)

        skill_body = None
        if skill_path:
            skills_dirs = [Path(__file__).parent.parent / "skills"]
            skill_registry = SkillRegistry(skills_dirs)
            skill = skill_registry.get_skill_by_path(skill_path)
            if skill:
                skill_body = skill.body

        privacy = config.privacy_mode or config.provider == "opencode"
        system_prompt = build_system_prompt(
            project=self.project, skill_body=skill_body, privacy_mode=privacy
        )

        return AgentLoop(
            provider=provider,
            tool_registry=registry,
            system_prompt=system_prompt,
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
            ("Session", ["/swarm", "/history", "/provider", "/model", "/help", "/quit"]),
        ]
        for section_name, cmds in sections:
            table.add_row(f"  [bold dim]{section_name}[/]", "")
            for cmd in cmds:
                table.add_row(f"    {cmd}", COMMAND_DESCRIPTIONS.get(cmd, ""))

        self.console.print(table)
        self.console.print()
        self.console.print("  [dim]Or just type a question in natural language.[/]\n")

    def _run_agent(self, message: str, skill_path: str | None = None):
        """Run the agent and display response with spinner."""
        try:
            if skill_path or self.agent_loop is None:
                loop = self._create_agent_loop(skill_path=skill_path)
                if not skill_path:
                    self.agent_loop = loop
            else:
                loop = self.agent_loop

            # Show spinner while agent thinks
            with self.console.status(
                "[dim #00d787]🧬 Analyzing...[/]",
                spinner="dots",
                spinner_style="#00d787",
            ):
                response = loop.chat(message)

            # Render response as markdown
            self.console.print()
            self.console.print(Markdown(response))
            self.console.print()

        except KeyboardInterrupt:
            self.console.print("\n[dim]Interrupted.[/]\n")
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/]\n")

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

    def run(self):
        """Main interactive loop."""
        self._print_banner()
        self._print_status()

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
            if cmd == "/swarm":
                self._handle_swarm()
                continue
            if cmd == "/history":
                self._handle_history(cmd_args)
                continue
            if cmd == "/provider":
                if cmd_args:
                    self.console.print(f"[#00d787]  Switched to provider: {cmd_args}[/]\n")
                    self.agent_loop = None
                else:
                    self._load_config()
                    self.console.print(f"  Provider: [bold]{self.config.provider}[/]\n")
                continue
            if cmd == "/model":
                if cmd_args:
                    self.console.print(f"[#00d787]  Switched to model: {cmd_args}[/]\n")
                    self.agent_loop = None
                else:
                    self._load_config()
                    self.console.print(f"  Model: [bold]{self.config.model}[/]\n")
                continue

            # Skill-mapped slash commands
            if cmd in COMMAND_SKILL_MAP:
                self.console.print()
                self._run_agent(f"{cmd} {cmd_args}".strip(), skill_path=COMMAND_SKILL_MAP[cmd])
                continue

            # Natural language
            self.console.print()
            self._run_agent(user_input)
