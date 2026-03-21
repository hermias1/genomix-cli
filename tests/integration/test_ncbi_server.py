"""Integration tests for NCBI database MCP server."""
from mcp_servers.base_database import BaseDatabaseServer


def test_base_database_cache_key():
    server = BaseDatabaseServer(name="test")
    key1 = server._cache_key("search", {"query": "BRCA1"})
    key2 = server._cache_key("search", {"query": "BRCA1"})
    key3 = server._cache_key("search", {"query": "TP53"})
    assert key1 == key2
    assert key1 != key3
