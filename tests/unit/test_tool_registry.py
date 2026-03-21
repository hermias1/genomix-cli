import pytest
from genomix.tools.registry import ToolRegistry


@pytest.fixture
def registry():
    return ToolRegistry()


def test_register_and_list(registry):
    registry.register(
        name="samtools_stats", description="Get alignment statistics",
        parameters={"type": "object", "properties": {"bam_path": {"type": "string"}}, "required": ["bam_path"]},
        handler=lambda args: '{"reads": 1000}',
    )
    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0]["function"]["name"] == "samtools_stats"


def test_dispatch_calls_handler(registry):
    registry.register(
        name="echo", description="Echo back",
        parameters={"type": "object", "properties": {"text": {"type": "string"}}},
        handler=lambda args: f"echo: {args['text']}",
    )
    result = registry.dispatch("echo", {"text": "hello"})
    assert result == "echo: hello"


def test_dispatch_unknown_tool(registry):
    with pytest.raises(KeyError, match="Unknown tool"):
        registry.dispatch("nonexistent", {})


def test_list_tools_returns_openai_format(registry):
    registry.register(name="my_tool", description="A tool", parameters={"type": "object", "properties": {}}, handler=lambda args: "")
    schema = registry.list_tools()[0]
    assert schema["type"] == "function"
    assert "function" in schema
    assert schema["function"]["name"] == "my_tool"
    assert schema["function"]["description"] == "A tool"
