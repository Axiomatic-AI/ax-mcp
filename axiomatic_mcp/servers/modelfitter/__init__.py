def main():
    """Main entry point for the AxModelFitterV2 server."""
    from .server import mcp

    mcp.run(transport="stdio")
