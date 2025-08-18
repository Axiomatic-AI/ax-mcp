def main():
    """Main entry point for the AxModelFitter server."""
    from .server import mcp

    mcp.run(transport="stdio")
