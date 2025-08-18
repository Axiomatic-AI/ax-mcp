"""Domain-specific MCP servers."""

from .pic.server import mcp as pic_mcp

servers = [
    pic_mcp,
]

__all__ = ["pic_mcp"]
