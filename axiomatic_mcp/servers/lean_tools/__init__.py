"""Lean Tools MCP Server - Standalone Lean tools for theorem proving."""

def main():
    """Main entry point for the Lean tools server."""
    from .server import mcp
    mcp.run(transport="stdio")