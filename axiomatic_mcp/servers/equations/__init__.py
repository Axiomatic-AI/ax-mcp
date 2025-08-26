def main():
    """Main entry point for the equations server."""
    from .server import mcp

    mcp.run(transport="stdio")
