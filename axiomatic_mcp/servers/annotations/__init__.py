def main():
    """Main entry point for the Annotations server."""
    from .server import mcp

    mcp.run(transport="stdio")
