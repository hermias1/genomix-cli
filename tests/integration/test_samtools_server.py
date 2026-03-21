import json
from unittest.mock import patch, MagicMock
import pytest
from mcp_servers.base_biotool import BaseBiotoolServer


def test_base_biotool_check_binary():
    with patch("shutil.which", return_value="/usr/bin/samtools"):
        server = BaseBiotoolServer(binary_name="samtools")
        assert server.check_binary() is True


def test_base_biotool_check_binary_missing():
    with patch("shutil.which", return_value=None):
        server = BaseBiotoolServer(binary_name="samtools")
        assert server.check_binary() is False


def test_base_biotool_run_command():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "1000 reads"
    mock_result.stderr = ""
    with patch("subprocess.run", return_value=mock_result):
        server = BaseBiotoolServer(binary_name="samtools")
        result = server.run_command(["stats", "input.bam"])
        assert "1000 reads" in result


def test_base_biotool_run_command_failure():
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "file not found"
    with patch("subprocess.run", return_value=mock_result):
        server = BaseBiotoolServer(binary_name="samtools")
        result = server.run_command(["stats", "missing.bam"])
        assert "error" in result.lower() or "file not found" in result.lower()
