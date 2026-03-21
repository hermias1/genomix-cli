import subprocess
import sys


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
