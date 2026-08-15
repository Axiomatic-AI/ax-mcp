def main():
    """Main entry point for the AxPaperSearch server."""
    from .server import mcp

    mcp.run(transport="stdio")
