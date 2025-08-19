"""PIC (Photonic Integrated Circuit) domain MCP server."""

from typing import Annotated

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...shared import AxiomaticAPIClient

mcp = FastMCP(
    name="Axiomatic PIC Designer",
    instructions="""This server provides tools to design, optimize,
    and simulate photonic integrated circuits.""",
    version="0.0.1",
)


@mcp.tool(
    name="design_circuit",
    description="Design a photonic integrated circuit and optionally create a Python file",
    tags=["design", "gfsfactory"],
)
async def design(
    query: Annotated[str, "The query to design the circuit"],
    existing_code: Annotated[str | None, "Existing code to use as a reference to refine"] = None,
) -> ToolResult:
    """Design a photonic integrated circuit."""
    data = {
        "query": query,
    }

    if existing_code:
        data["code"] = existing_code

    response = AxiomaticAPIClient().post("/pic/circuit/refine", data=data)
    code: str = response["code"]

    file_name = "circuit.py"

    return ToolResult(
        content=[TextContent(type="text", text=f"Generated photonic circuit design for: {file_name}\n\n```python\n{code}\n```")],
        structured_content={
            "suggestions": [
                {"type": "create_file", "path": file_name, "content": code, "description": f"Create {file_name} with the generated circuit design"}
            ]
        },
    )
