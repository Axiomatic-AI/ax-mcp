def main():
    """Main entry point for the AxEquationExplorer server."""
    from .server import mcp

    mcp.run(transport="stdio", show_banner=False)
