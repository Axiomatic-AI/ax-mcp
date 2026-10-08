def main():
    """Main entry point for the AxMeep server."""
    from .server import mcp

    mcp.run(transport="stdio", show_banner=False)
