"""Axiomatic MCP Servers - Modular MCP servers built with FastMCP."""

__version__ = "0.1.3"

import asyncio

from fastmcp import FastMCP

from .providers.middleware_provider import get_mcp_middleware
from .servers import servers

axiomatic_mcp = FastMCP(
    name="Axiomatic MCP",
    instructions="""This server provides various tools to help with physics and engineering workflows..""",
    version=__version__,
    middleware=get_mcp_middleware(),
)


async def setup():
    for server in servers:
        await axiomatic_mcp.import_server(server["server"], prefix=server["name"])


def main():
    """Main entry point for the all-in-one server."""
    asyncio.run(setup())
    axiomatic_mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
