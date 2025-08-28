def main():
    """Main entry point for the Prover server."""
    from .server import mcp

    mcp.run(transport="stdio")
