from genomix.agent.context_compressor import should_compress, compress_messages


def test_should_compress_under_limit():
    assert should_compress([{"role": "user", "content": "Hi"}], max_tokens=200_000) is False


def test_should_compress_over_limit():
    big = [{"role": "tool", "content": "x" * 100_000}] * 5
    assert should_compress(big, max_tokens=200_000) is True


def test_compress_preserves_recent():
    messages = [
        {"role": "system", "content": "You are Genomix"},
        {"role": "user", "content": "old question"},
        {"role": "assistant", "content": "old answer"},
        {"role": "tool", "content": "x" * 50_000, "tool_call_id": "c1"},
        {"role": "user", "content": "new question"},
    ]
    compressed = compress_messages(messages, max_tokens=1000)
    assert compressed[0]["role"] == "system"
    assert compressed[-1]["content"] == "new question"
    assert len(compressed) <= len(messages)
