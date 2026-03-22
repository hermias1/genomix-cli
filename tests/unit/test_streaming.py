from genomix.providers.base import (
    StreamEvent, TextDelta, ToolCallStart, ToolCallArgs,
    ToolCallComplete, ToolResult, ErrorEvent, StreamDone,
)

def test_text_delta():
    e = TextDelta(text="hello")
    assert e.text == "hello"
    assert isinstance(e, StreamEvent)

def test_tool_call_start():
    e = ToolCallStart(id="c1", name="read_file")
    assert e.name == "read_file"

def test_tool_call_args():
    e = ToolCallArgs(id="c1", partial_args='{"path":')
    assert e.partial_args == '{"path":'

def test_tool_call_complete():
    e = ToolCallComplete(id="c1", name="read_file", arguments={"path": "x.vcf"})
    assert e.arguments["path"] == "x.vcf"

def test_tool_result():
    e = ToolResult(tool_name="read_file", result="contents...")
    assert e.tool_name == "read_file"

def test_error_event():
    e = ErrorEvent(message="timeout")
    assert e.message == "timeout"

def test_stream_done():
    e = StreamDone()
    assert isinstance(e, StreamEvent)
