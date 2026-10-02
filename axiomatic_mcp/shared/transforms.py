from collections.abc import Sequence

from fastmcp.server.transforms import GetToolNext, Transform
from fastmcp.tools import Tool
from fastmcp.utilities.versions import VersionSpec


def standalone_title(tool: Tool) -> str:
    """The title a client sees for ``tool`` on its own server, as FastMCP derives it."""
    if tool.title:
        return tool.title
    if tool.annotations and tool.annotations.title:
        return tool.annotations.title
    return tool.name.replace("_", " ").replace("-", " ").title()


class ServerTitle(Transform):
    """Titles every tool ``"<server>: <standalone title>"``.

    Apply it before the namespace. FastMCP derives a missing title from the tool's final name, so a
    namespaced ``AxTidy3D_start_simulation`` would otherwise read "Axtidy3D Start Simulation", and
    the twelve ``*_report_feedback`` tools would all read alike apart from that garbled prefix.
    """

    def __init__(self, server_name: str) -> None:
        self._server_name = server_name

    def __repr__(self) -> str:
        return f"ServerTitle({self._server_name!r})"

    def _retitle(self, tool: Tool) -> Tool:
        return tool.model_copy(update={"title": f"{self._server_name}: {standalone_title(tool)}"})

    async def list_tools(self, tools: Sequence[Tool]) -> Sequence[Tool]:
        return [self._retitle(tool) for tool in tools]

    async def get_tool(self, name: str, call_next: GetToolNext, *, version: VersionSpec | None = None) -> Tool | None:
        tool = await call_next(name, version=version)
        return self._retitle(tool) if tool else None
