def main():
    """Main entry point for the DT Optimizer server."""
    from .server import mcp

    mcp.run(transport="stdio")
