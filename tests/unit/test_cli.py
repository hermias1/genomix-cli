import subprocess
import sys

from genomix.project.setup_wizard import check_binary


def test_check_binary_returns_tuple():
    name, found, version = check_binary("python3")
    assert name == "python3"
    assert isinstance(found, bool)


def test_genomix_help():
    """genomix --help should exit 0 and show usage."""
    result = subprocess.run(
        [sys.executable, "-m", "genomix.cli", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "genomix" in result.stdout.lower()


def test_genomix_version():
    """genomix --version should print the version string."""
    result = subprocess.run(
        [sys.executable, "-m", "genomix.cli", "--version"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


from unittest.mock import patch, MagicMock

from genomix.cli import build_parser, COMMAND_SKILL_MAP, SLASH_COMMANDS


def test_parser_subcommands():
    parser = build_parser()
    for cmd in ["setup", "init"]:
        args = parser.parse_args([cmd])
        assert args.command == cmd


def test_command_skill_map_has_all_analysis_commands():
    expected = ["/qc", "/align", "/variant-call", "/annotate", "/blast", "/msa", "/phylo", "/summary", "/search", "/explain"]
    for cmd in expected:
        assert cmd in COMMAND_SKILL_MAP


def test_slash_commands_list():
    assert "/help" in SLASH_COMMANDS
    assert "/quit" in SLASH_COMMANDS
