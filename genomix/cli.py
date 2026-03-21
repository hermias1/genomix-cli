"""Genomix CLI entry point."""

import argparse
import sys
from pathlib import Path

from genomix import __version__

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from rich.console import Console


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


def create_agent_loop(skill_path=None):
    """Factory: create a fully wired agent loop."""
    from genomix.config import load_config, load_secrets
    from genomix.providers import get_provider
    from genomix.tools.registry import ToolRegistry
    from genomix.tools.file_tools import register_file_tools
    from genomix.skills.registry import SkillRegistry
    from genomix.project.manager import ProjectManager, ProjectNotFoundError
    from genomix.agent.prompt_builder import build_system_prompt
    from genomix.agent.loop import AgentLoop

    config = load_config()
    secrets = load_secrets()
    api_key = secrets.get(f"{config.provider}_api_key", secrets.get("anthropic_api_key", ""))
    provider = get_provider(config.provider, api_key=api_key, model=config.model)

    registry = ToolRegistry()
    register_file_tools(registry)

    project = None
    try:
        project = ProjectManager.discover(Path.cwd())
    except ProjectNotFoundError:
        pass

    skill_body = None
    if skill_path:
        skills_dirs = [Path(__file__).parent.parent / "skills"]
        skill_registry = SkillRegistry(skills_dirs)
        skill = skill_registry.get_skill_by_path(skill_path)
        if skill:
            skill_body = skill.body

    privacy = config.privacy_mode or config.provider == "opencode"
    system_prompt = build_system_prompt(project=project, skill_body=skill_body, privacy_mode=privacy)
    return AgentLoop(provider=provider, tool_registry=registry, system_prompt=system_prompt)


def handle_run(slash_command, args, output_format="text"):
    skill_path = COMMAND_SKILL_MAP.get(slash_command)
    loop = create_agent_loop(skill_path=skill_path)
    message = f"{slash_command} {' '.join(args)}".strip()
    result = loop.chat(message)
    if output_format == "json":
        import json
        return json.dumps({"command": slash_command, "response": result})
    return result


def handle_ask(question):
    loop = create_agent_loop()
    return loop.chat(question)


def handle_init(path=None):
    """Interactive project initialization."""
    console = Console()
    console.print("[bold]🧬 New Genomix Project[/bold]\n")
    name = input("Project name: ")
    organism = input("Organism: ")
    ref = input("Reference genome: ")
    dtype = input("Data type: ")
    from genomix.project.manager import ProjectManager
    pm = ProjectManager(Path(path) if path else Path.cwd())
    project = pm.init(name=name, organism=organism, reference_genome=ref, data_type=dtype)
    console.print(f"\n[green]✓[/green] Project initialized: {project.name}")


def handle_interactive():
    """Start interactive TUI session."""
    console = Console()
    console.print(f"[bold]🧬 Genomix CLI v{__version__}[/bold]")
    console.print("Type your question or use /help\n")

    completer = WordCompleter(SLASH_COMMANDS, sentence=True)
    session = PromptSession(completer=completer)
    agent_loop = None  # Lazy init on first non-command message

    while True:
        try:
            user_input = session.prompt("genomix> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input in ("/quit", "/exit", "/q"):
            break
        if user_input == "/help":
            for cmd in SLASH_COMMANDS[:-1]:  # exclude /quit
                console.print(f"  {cmd}")
            continue

        # Slash command with skill
        parts = user_input.split(maxsplit=1)
        cmd = parts[0]
        cmd_args = parts[1] if len(parts) > 1 else ""

        if cmd == "/swarm":
            from genomix.swarm.manager import SwarmManager
            from genomix.project.manager import ProjectManager, ProjectNotFoundError
            try:
                project = ProjectManager.discover(Path.cwd())
                sm = SwarmManager(state_dir=project.root / ".genomix" / "runtime" / "swarm")
                tasks = sm.list_tasks()
                if not tasks:
                    console.print("No running analyses.")
                else:
                    for t in tasks:
                        console.print(f"  #{t.id}  {t.command}  {t.status.value}")
            except ProjectNotFoundError:
                console.print("No project found. Run 'genomix init' first.")
            continue

        if cmd == "/history":
            from genomix.agent.session_store import SessionStore
            from genomix.project.manager import ProjectManager, ProjectNotFoundError
            try:
                project = ProjectManager.discover(Path.cwd())
                store = SessionStore(project.root / ".genomix" / "runtime" / "sessions.db")
                if cmd_args:
                    results = store.search(cmd_args)
                    for r in results:
                        console.print(f"  {r['id']}  {r['title']}")
                else:
                    sessions = store.list_sessions()
                    for s in sessions:
                        console.print(f"  {s['id']}  {s['title']}  {s['created_at']}")
            except ProjectNotFoundError:
                console.print("No project found.")
            continue

        if cmd == "/provider":
            if cmd_args:
                console.print(f"Switched to provider: {cmd_args}")
                agent_loop = None  # Force re-init with new provider
            else:
                from genomix.config import load_config
                console.print(f"Current provider: {load_config().provider}")
            continue

        if cmd == "/model":
            if cmd_args:
                console.print(f"Switched to model: {cmd_args}")
                agent_loop = None
            else:
                from genomix.config import load_config
                console.print(f"Current model: {load_config().model}")
            continue

        if cmd in COMMAND_SKILL_MAP:
            skill_path = COMMAND_SKILL_MAP[cmd]
            try:
                loop = create_agent_loop(skill_path=skill_path)
                response = loop.chat(f"{cmd} {cmd_args}".strip())
                console.print(response)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
            continue

        # Natural language → agent loop
        try:
            if agent_loop is None:
                agent_loop = create_agent_loop()
            response = agent_loop.chat(user_input)
            console.print(response)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


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
        print("Setup wizard not yet implemented.")
        return 0
    if args.command == "run":
        print(handle_run(args.slash_command, args.args or [], args.format))
        return 0
    if args.command == "ask":
        question = " ".join(args.question) if args.question else sys.stdin.read().strip()
        print(handle_ask(question))
        return 0
    print(f"Command '{args.command}' not yet implemented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
