"""Electronics domain MCP server."""

from .server import ElectronicsServer


def main():
    """Entry point for electronics domain server."""
    server = ElectronicsServer()
    server.run()


__all__ = ["ElectronicsServer", "main"]