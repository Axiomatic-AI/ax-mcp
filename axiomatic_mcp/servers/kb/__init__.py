def main():
    """Main entry point for the AxKnowledgeBase server."""
    from .server import mcp

    mcp.run(transport="stdio")
