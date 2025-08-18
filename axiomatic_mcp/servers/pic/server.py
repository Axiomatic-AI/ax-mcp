"""PIC (Photonic Integrated Circuit) domain MCP server."""

from typing import Annotated, Optional
from fastmcp import FastMCP


from ...shared import (
    AxiomaticAPIClient,
)

mcp = FastMCP(
    name="Axiomatic PIC Designer",
    description="MCP server that aids in the design of photonic integrated circuits",
    instructions="This server provides tools to design, optimize, and simulate photonic integrated circuits.",
    version="0.0.1",
)

@mcp.tool(
    name="design_circuit",
    description="Design a photonic integrated circuit",
    tags=["design", "gfsfactory"],
)
async def design(
    query: Annotated[str, "The query to design the circuit"],
    existing_code: Annotated[Optional[str], "Existing code to use as a reference and to refine with the query"] = None
) -> Annotated[str, "The code for the designed circuit"]:
    """Design a photonic integrated circuit."""
    data = {
        "query": query,
        "code": existing_code,
    }
    response = AxiomaticAPIClient().post("/pic/circuit/refine", data=data)
    return response["code"]