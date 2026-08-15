"""Domain-specific MCP servers."""

from typing import TypedDict

from fastmcp import FastMCP

from .annotations.server import mcp as annotations_mcp
from .argmin.server import mcp as argmin_mcp
from .axmodelfitter.server import mcp as axmodelfitter_mcp
from .documents.server import mcp as documents_mcp
from .equations.server import mcp as equations_mcp
from .kb.server import mcp as kb_mcp
from .modelfitter.server import mcp as modelfitter_mcp
from .paper_search.server import mcp as paper_search_mcp
from .plots.server import plots as plots_mcp
from .tidy3d.server import mcp as tidy3d_mcp


class ServerConfig(TypedDict):
    domain: str
    name: str
    server: FastMCP


servers: list[ServerConfig] = [
    ServerConfig(domain="equations", name="AxEquationExplorer", server=equations_mcp),
    ServerConfig(domain="documents", name="AxDocumentParser", server=documents_mcp),
    ServerConfig(domain="annotations", name="AxDocumentAnnotator", server=annotations_mcp),
    ServerConfig(domain="axmodelfitter", name="AxModelFitterLegacy", server=axmodelfitter_mcp),
    ServerConfig(domain="plots", name="AxPlotToData", server=plots_mcp),
    ServerConfig(domain="argmin", name="AxArgmin", server=argmin_mcp),
    ServerConfig(domain="modelfitter", name="AxModelFitter", server=modelfitter_mcp),
    ServerConfig(domain="kb", name="AxKnowledgeBase", server=kb_mcp),
    ServerConfig(domain="paper_search", name="AxPaperSearch", server=paper_search_mcp),
    ServerConfig(domain="tidy3d", name="AxTidy3D", server=tidy3d_mcp),
]


__all__ = ["ServerConfig", "servers"]
