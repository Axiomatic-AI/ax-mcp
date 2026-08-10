def main():
    """Main entry point for the AxPde server."""
    from .server import mcp

    mcp.run(transport="stdio")
