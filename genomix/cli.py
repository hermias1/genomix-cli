"""Genomix CLI entry point."""

import argparse
import sys

from genomix import __version__


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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        print(f"🧬 Genomix CLI v{__version__}")
        print("Interactive mode not yet implemented. Use --help for available commands.")
        return 0

    print(f"Command '{args.command}' not yet implemented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
