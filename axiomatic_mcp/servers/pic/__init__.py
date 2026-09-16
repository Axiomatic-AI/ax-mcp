def main():
    """Main entry point for the PIC server."""
    from .server import mcp

    mcp.run(transport="stdio")
