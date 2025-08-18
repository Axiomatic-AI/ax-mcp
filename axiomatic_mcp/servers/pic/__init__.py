"""PIC (Photonic Integrated Circuit) domain MCP server."""

from .server import PICServer


def main():
    """Entry point for PIC domain server."""
    server = PICServer()
    server.run()


__all__ = ["PICServer", "main"]