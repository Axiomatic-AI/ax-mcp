def main():
    """Main entry point for the AxArgmin server."""
    from .server import mcp

    mcp.run(transport="stdio")
