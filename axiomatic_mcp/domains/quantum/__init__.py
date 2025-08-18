"""Quantum domain MCP server."""

from .server import QuantumServer


def main():
    """Entry point for quantum domain server."""
    server = QuantumServer()
    server.run()


__all__ = ["QuantumServer", "main"]