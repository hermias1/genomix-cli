from unittest.mock import patch, MagicMock
from genomix.cli import handle_run, handle_ask

def test_handle_run_returns_string():
    with patch("genomix.cli.create_agent_loop") as mock:
        loop = MagicMock()
        loop.chat.return_value = "QC complete"
        mock.return_value = loop
        result = handle_run("/qc", ["data/reads.fastq"])
        assert result == "QC complete"

def test_handle_ask_returns_string():
    with patch("genomix.cli.create_agent_loop") as mock:
        loop = MagicMock()
        loop.chat.return_value = "42 variants"
        mock.return_value = loop
        result = handle_ask("How many variants?")
        assert result == "42 variants"

def test_handle_run_json_format():
    with patch("genomix.cli.create_agent_loop") as mock:
        loop = MagicMock()
        loop.chat.return_value = "Done"
        mock.return_value = loop
        result = handle_run("/qc", [], output_format="json")
        assert '"response"' in result
