import pytest
from genomix.tools.mcp_bridge import MCPBridge, MCPServerConfig


def test_server_config():
    config = MCPServerConfig(name="samtools", command="python", args=["-m", "mcp_servers.biotools.samtools_server"], enabled=True)
    assert config.name == "samtools"
    assert config.enabled is True


def test_bridge_register_server():
    bridge = MCPBridge()
    config = MCPServerConfig(name="samtools", command="python", args=["-m", "mcp_servers.biotools.samtools_server"], enabled=True)
    bridge.register_server(config)
    assert "samtools" in bridge.registered_servers


def test_bridge_disabled_server_not_registered():
    bridge = MCPBridge()
    config = MCPServerConfig(name="cosmic", command="python", args=[], enabled=False)
    bridge.register_server(config)
    assert "cosmic" in bridge.registered_servers
    assert not bridge.registered_servers["cosmic"].enabled
