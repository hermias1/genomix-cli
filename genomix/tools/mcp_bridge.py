"""MCP Bridge: manages MCP server connections and proxies tool calls into the ToolRegistry."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from genomix.tools.registry import ToolRegistry


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    enabled: bool = True
    env: dict[str, str] | None = None


class MCPBridge:
    def __init__(self) -> None:
        self.registered_servers: dict[str, MCPServerConfig] = {}
        self._sessions: dict[str, ClientSession] = {}
        self._exit_stacks: dict[str, Any] = {}

    def register_server(self, config: MCPServerConfig) -> None:
        """Register an MCP server configuration (does not connect)."""
        self.registered_servers[config.name] = config

    async def connect_server(self, name: str) -> ClientSession:
        """Spawn the server process and return an active ClientSession."""
        config = self.registered_servers[name]
        params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env,
        )
        from contextlib import AsyncExitStack

        stack = AsyncExitStack()
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self._sessions[name] = session
        self._exit_stacks[name] = stack
        return session

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Call a tool on a connected MCP server."""
        if server_name not in self._sessions:
            await self.connect_server(server_name)
        session = self._sessions[server_name]
        return await session.call_tool(tool_name, arguments)

    async def register_tools_to_registry(self, server_name: str, registry: ToolRegistry) -> None:
        """Connect to a server, list its tools, and register proxy handlers in the ToolRegistry."""
        if server_name not in self._sessions:
            await self.connect_server(server_name)
        session = self._sessions[server_name]
        result = await session.list_tools()
        for tool in result.tools:
            # Capture tool.name in a closure so each handler refers to its own tool
            def make_handler(t_name: str):
                def handler(args: dict[str, Any]) -> str:
                    return str(asyncio.get_event_loop().run_until_complete(
                        self.call_tool(server_name, t_name, args)
                    ))
                return handler

            registry.register(
                name=tool.name,
                description=tool.description or "",
                parameters=tool.inputSchema if isinstance(tool.inputSchema, dict) else tool.inputSchema.model_dump(),
                handler=make_handler(tool.name),
            )

    async def shutdown(self) -> None:
        """Close all open server connections."""
        for name, stack in list(self._exit_stacks.items()):
            await stack.aclose()
        self._sessions.clear()
        self._exit_stacks.clear()
