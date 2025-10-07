"""Domain-specific MCP servers."""

from typing import TypedDict

from fastmcp import FastMCP

from .annotations.server import mcp as annotations_mcp
from .documents.server import mcp as documents_mcp
from .equations.server import mcp as equations_mcp
from .plots.server import plots as plots_mcp


class ServerConfig(TypedDict):
    domain: str
    name: str
    server: FastMCP


servers: list[ServerConfig] = [
    ServerConfig(domain="equations", name="AxEquationExplorer", server=equations_mcp),
    ServerConfig(domain="documents", name="AxDocumentParser", server=documents_mcp),
    ServerConfig(domain="annotations", name="AxDocumentAnnotator", server=annotations_mcp),
    ServerConfig(domain="plots", name="AxPlotToData", server=plots_mcp),
]


__all__ = ["ServerConfig", "servers"]
