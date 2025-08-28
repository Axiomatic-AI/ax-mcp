"""Entry point for running leanclient as a module."""

from .server import mcp

if __name__ == "__main__":
    mcp.run()
