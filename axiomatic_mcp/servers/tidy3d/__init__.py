def main():
    """Main entry point for the AxTidy3D server."""
    from .server import mcp

    mcp.run(transport="stdio")
