def main():
    """Main entry point for the AxBlueprints server."""
    from .server import mcp

    mcp.run(transport="stdio")
