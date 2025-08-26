def main():
    """Main entry point for the PIC server."""
    from .server import mcp

    print("DEBUG describe:", mcp._tool_manager.list_tools())
    mcp.run(transport="stdio")
