"""Code Execution MCP server."""

from typing import Annotated

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...shared import AxiomaticAPIClient

mcp = FastMCP(
    name="Axiomatic Code Execution",
    instructions="""This server provides tools to execute Python code
    securely in a sandboxed environment with limited supported libraries.""",
    version="0.0.1",
)


@mcp.tool(
    name="code_execution",
    description="Execute Python code in a secure environment and return stdout or error trace",
    tags=["python", "execute", "sandbox"],
)
async def execute_code(
    code: Annotated[str, "The Python code to execute"],
) -> ToolResult:
    """Execute Python code securely in the Axiomatic environment."""

    data = {"code": code}
    response = AxiomaticAPIClient().post("/code-execution/python/execute", data=data)

    output: str = response.get("output", "")
    is_success: bool = response.get("is_success", False)
    error_trace: str | None = response.get("error_trace")

    text_output = f"Execution Result:\n\n{output}" if is_success else f"Execution Failed:\n\n{error_trace}"

    return ToolResult(
        content=[TextContent(type="text", text=text_output)],
        structured_content={
            "execution_result": {
                "output": output,
                "is_success": is_success,
                "error_trace": error_trace,
            }
        },
    )
