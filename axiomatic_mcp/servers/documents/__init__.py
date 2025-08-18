def main():
    """Main entry point for the AxDocumentParser server."""
    from .server import mcp

    mcp.run(transport="stdio")
