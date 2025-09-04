def main():
    """Main entry point for the Documents server."""
    from .server import mcp

    mcp.run(transport="stdio")
