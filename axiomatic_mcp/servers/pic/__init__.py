if __name__ == "__main__":
    from .server import mcp
    mcp.run(transport="stdio")