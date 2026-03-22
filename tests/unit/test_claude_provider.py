import json

from genomix.providers.claude import ClaudeProvider


def test_claude_build_request_extracts_system_and_tool_results():
    messages = [
        {"role": "system", "content": "You are Genomix"},
        {"role": "user", "content": "Analyze this BAM"},
        {
            "role": "assistant",
            "content": "Calling a tool",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "samtools_stats",
                        "arguments": json.dumps({"bam": "sample.bam"}),
                    },
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": '{"reads": 1000}'},
    ]

    request = ClaudeProvider.build_request(messages, tools=None, model="claude-sonnet-4-6")

    assert request["system"] == "You are Genomix"
    assert request["messages"][0] == {"role": "user", "content": "Analyze this BAM"}

    assistant_message = request["messages"][1]
    assert assistant_message["role"] == "assistant"
    assert assistant_message["content"][0]["type"] == "text"
    assert assistant_message["content"][1]["type"] == "tool_use"
    assert assistant_message["content"][1]["name"] == "samtools_stats"
    assert assistant_message["content"][1]["input"] == {"bam": "sample.bam"}

    tool_result_message = request["messages"][2]
    assert tool_result_message["role"] == "user"
    assert tool_result_message["content"][0]["type"] == "tool_result"
    assert tool_result_message["content"][0]["tool_use_id"] == "call_1"


def test_claude_build_request_converts_tools_to_input_schema():
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file",
                "parameters": {"type": "object", "properties": {"path": {"type": "string"}}},
            },
        }
    ]

    request = ClaudeProvider.build_request(
        [{"role": "user", "content": "Read x"}],
        tools=tools,
        model="claude-sonnet-4-6",
    )

    assert request["tools"][0]["name"] == "read_file"
    assert request["tools"][0]["input_schema"]["type"] == "object"
