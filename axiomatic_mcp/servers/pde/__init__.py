def main():
    """Main entry point for the AxPDE server."""
    from .server import mcp

    mcp.run(transport="stdio")
