def main():
    """Main entry point for the Lean client server."""
    from .server import mcp

    mcp.run(transport="stdio")
