def main():
    """Main entry point for the plot_parser server."""
    from .server import mcp

    mcp.run(transport="stdio")
