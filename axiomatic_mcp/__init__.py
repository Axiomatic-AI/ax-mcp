"""Axiomatic MCP Servers - Modular MCP servers built with FastMCP."""

__version__ = "0.1.17"

import asyncio

from fastmcp import FastMCP

from .providers.middleware_provider import get_mcp_middleware
from .servers import servers

axiomatic_mcp = FastMCP(
    name="Axiomatic MCP",
    instructions="""This server provides various tools to help with physics and engineering workflows.

    For model fitting: use the AxModelFitter_* tools for new workflows. The AxModelFitterLegacy_* tools are the
    deprecated continuation of the original AxModelFitter toolset — existing workflows built on them should keep
    using them this release; they will be removed in the next major release.""",
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
