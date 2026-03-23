from unittest.mock import patch, MagicMock
from genomix.cli import create_agent_loop, handle_run, handle_ask
from genomix.config import GenomixConfig
from genomix.project.manager import ProjectNotFoundError

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


def test_handle_run_passes_output_override_in_prompt():
    with patch("genomix.cli.create_agent_loop") as mock:
        loop = MagicMock()
        loop.chat.return_value = "Done"
        mock.return_value = loop

        handle_run("/align", ["reads.fastq.gz"], output_format="text", output_override="/tmp/out.bam")

        prompt = loop.chat.call_args.args[0]
        assert "/tmp/out.bam" in prompt


def test_create_agent_loop_treats_remote_ollama_as_non_local():
    config = GenomixConfig(provider="ollama", endpoint="https://ollama.example.org")

    with patch("genomix.config.load_config", return_value=config), \
         patch("genomix.config.load_secrets", return_value={}), \
         patch("genomix.providers.get_provider", return_value=MagicMock()), \
         patch("genomix.runtime.build_tool_registry", return_value=(MagicMock(), None)), \
         patch("genomix.project.manager.ProjectManager.discover", side_effect=ProjectNotFoundError("no project")), \
         patch("genomix.agent.prompt_builder.build_system_prompt", return_value="system") as build_prompt, \
         patch("genomix.agent.loop.AgentLoop", return_value=MagicMock()):
        create_agent_loop()

    assert build_prompt.call_args.kwargs["privacy_mode"] is False
