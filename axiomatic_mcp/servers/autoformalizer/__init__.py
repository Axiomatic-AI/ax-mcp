def main():
    """Main entry point for the Autoformalizer server."""
    from .server import mcp

    mcp.run(transport="stdio")
