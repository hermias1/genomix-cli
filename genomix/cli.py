"""Genomix CLI entry point."""

import argparse
import sys
from pathlib import Path

from genomix import __version__
from rich.console import Console


SLASH_COMMANDS = [
    "/qc", "/align", "/variant-call", "/annotate", "/pipeline",
    "/blast", "/msa", "/phylo", "/summary", "/search", "/explain", "/report",
    "/lookup", "/drug", "/disease", "/literature", "/frequency", "/cancer", "/domains", "/structure",
    "/swarm", "/history", "/provider", "/model", "/help", "/quit",
]

COMMAND_SKILL_MAP = {
    "/qc": "sequencing/quality-control",
    "/align": "sequencing/alignment",
    "/variant-call": "sequencing/variant-calling",
    "/annotate": "sequencing/annotation",
    "/pipeline": "sequencing/pipeline",
    "/blast": "comparative/blast-analysis",
    "/msa": "comparative/multiple-alignment",
    "/phylo": "comparative/phylogenetics",
    "/summary": "exploration/sequence-summary",
    "/search": "exploration/database-search",
    "/explain": "exploration/variant-explain",
    "/report": "reporting/clinical-report",
    "/lookup": "exploration/variant-lookup",
    "/drug": "pharmacogenomics/drug-interaction",
    "/disease": "exploration/disease-association",
    "/literature": "exploration/literature-search",
    "/frequency": "exploration/population-frequency",
    "/cancer": "oncology/cancer-mutations",
    "/domains": "structural/protein-domains",
    "/structure": "structural/protein-structure",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genomix",
        description="AI-powered CLI for DNA sequence and genome analysis",
    )
    parser.add_argument(
        "--version", action="version", version=f"genomix {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("setup", help="Install dependencies and configure AI provider")
    subparsers.add_parser("init", help="Initialize a new genomix project")

    run_parser = subparsers.add_parser("run", help="Run a slash command non-interactively")
    run_parser.add_argument("slash_command", help="Slash command (e.g. /qc)")
    run_parser.add_argument("args", nargs="*", help="Command arguments")
    run_parser.add_argument("--output", "-o", help="Output path override")
    run_parser.add_argument("--format", choices=["text", "json"], default="text")

    ask_parser = subparsers.add_parser("ask", help="Ask a question non-interactively")
    ask_parser.add_argument("question", nargs="*", help="Question text")

    return parser


def create_agent_loop(skill_path=None, max_iterations=None):
    """Factory: create a fully wired agent loop."""
    from genomix.config import load_config, load_secrets
    from genomix.providers import get_provider
    from genomix.runtime import build_tool_registry, get_skill_dirs, is_local_provider
    from genomix.skills.registry import SkillRegistry
    from genomix.project.manager import ProjectManager, ProjectNotFoundError
    from genomix.agent.prompt_builder import build_system_prompt
    from genomix.agent.loop import AgentLoop

    config = load_config()
    secrets = load_secrets()
    KEY_MAP = {"claude": "anthropic_api_key", "openai": "openai_api_key", "ollama": None}
    key_name = KEY_MAP.get(config.provider)
    api_key = secrets.get(key_name, "") if key_name else ""
    provider_kwargs = {"api_key": api_key, "model": config.model}
    if config.endpoint:
        provider_kwargs["endpoint"] = config.endpoint
    provider = get_provider(config.provider, **provider_kwargs)

    registry, _ = build_tool_registry(auto_connect_mcp=True)

    project = None
    try:
        project = ProjectManager.discover(Path.cwd())
    except ProjectNotFoundError:
        pass

    skill_body = None
    if skill_path:
        skills_dirs = get_skill_dirs()
        skill_registry = SkillRegistry(skills_dirs)
        skill = skill_registry.get_skill_by_path(skill_path)
        if skill:
            skill_body = skill.body

    privacy = config.privacy_mode or is_local_provider(config.provider)
    system_prompt = build_system_prompt(project=project, skill_body=skill_body, privacy_mode=privacy)
    return AgentLoop(
        provider=provider,
        tool_registry=registry,
        system_prompt=system_prompt,
        max_iterations=max_iterations or 30,
    )


def handle_run(slash_command, args, output_format="text", output_override=None):
    from genomix.runtime import iteration_budget_for

    skill_path = COMMAND_SKILL_MAP.get(slash_command)
    message = f"{slash_command} {' '.join(args)}".strip()
    if output_override:
        message = f"{message}\nUse this exact output path: {output_override}"
    loop = create_agent_loop(
        skill_path=skill_path,
        max_iterations=iteration_budget_for(message, skill_path=skill_path),
    )
    result = loop.chat(message)
    if output_format == "json":
        import json
        return json.dumps({"command": slash_command, "response": result})
    return result


def handle_ask(question):
    from genomix.runtime import iteration_budget_for

    loop = create_agent_loop(max_iterations=iteration_budget_for(question))
    return loop.chat(question)


def handle_init(path=None):
    """Interactive project initialization."""
    console = Console()
    console.print("[bold]🧬 New Genomix Project[/bold]\n")
    try:
        name = input("Project name: ").strip()
        organism = input("Organism: ").strip()
        ref = input("Reference genome: ").strip()
        dtype = input("Data type: ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Cancelled.[/dim]")
        return
    if not name:
        console.print("[dim]Cancelled.[/dim]")
        return
    from genomix.project.manager import ProjectManager
    pm = ProjectManager(Path(path) if path else Path.cwd())
    project = pm.init(name=name, organism=organism, reference_genome=ref, data_type=dtype)
    console.print(f"\n[green]✓[/green] Project initialized: {project.name}")


def handle_setup() -> None:
    """Show dependency status and persist default configuration."""
    from genomix.config import GenomixConfig, load_config, save_config
    from genomix.project.setup_wizard import REQUIRED_BINARIES, check_binary, detect_os

    console = Console()
    config = load_config()
    if not config.provider:
        config = GenomixConfig()
        save_config(config)

    console.print("[bold]Genomix Setup[/bold]\n")
    console.print(f"OS: [cyan]{detect_os()}[/cyan]")
    console.print(f"Default provider: [cyan]{config.provider}[/cyan]")
    console.print(f"Default model: [cyan]{config.model}[/cyan]\n")

    for binary, version_command in REQUIRED_BINARIES:
        version_args = version_command.split()[1:]
        name, found, version = check_binary(binary, version_args=version_args)
        status = "[green]found[/green]" if found else "[yellow]missing[/yellow]"
        suffix = f" [dim]{version}[/dim]" if version else ""
        console.print(f"- {name}: {status}{suffix}")

    console.print("\n[dim]Install missing binaries and ensure Ollama is running if you use the default local provider.[/dim]")


def handle_interactive():
    """Start immersive interactive TUI session."""
    from genomix.tui import GenomixTUI
    tui = GenomixTUI()
    tui.run()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        handle_interactive()
        return 0
    if args.command == "init":
        handle_init()
        return 0
    if args.command == "setup":
        handle_setup()
        return 0
    if args.command == "run":
        print(handle_run(args.slash_command, args.args or [], args.format, args.output))
        return 0
    if args.command == "ask":
        question = " ".join(args.question) if args.question else sys.stdin.read().strip()
        print(handle_ask(question))
        return 0
    print(f"Command '{args.command}' not yet implemented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
