def main():
    """Main entry point for the Code Execution server."""
    from .server import mcp

    mcp.run(transport="stdio")
