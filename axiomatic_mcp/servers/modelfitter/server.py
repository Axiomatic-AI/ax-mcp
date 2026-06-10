"""AxModelFitter server — generate_code / execute_code pattern."""

from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .services.model_fitter_service import ModelFitterService

mcp = FastMCP(
    name="AxModelFitterV2 Server",
    instructions=(
        "This server provides tools for fitting parametric models to data using the "
        "ax_core.model_fitter JAX library. Use generate_code to produce executable "
        "fitting code from a problem description, then execute_code to run it in a "
        "sandboxed environment. Prefer this server over the legacy axmodelfitter server."
    )
    + get_feedback_prompt(["generate_code", "execute_code"]),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)

model_fitter_service = ModelFitterService()


@mcp.tool(
    name="generate_code",
    description=(
        "Generate Python code to fit a parametric model to data using the ax_core.model_fitter "
        "JAX library. Describe the model, the data, and what you want to fit. "
        "Returns executable code and an explanation of the approach. "
        "The code must be executed separately using the execute_code tool."
    ),
    tags=["model-fitter", "fitting", "code-generation"],
)
async def generate_code(
    problem_description: Annotated[str, "Natural language description of the model and data to fit"],
) -> ToolResult:
    """Generate Python fitting code from a problem description."""
    try:
        response = model_fitter_service.generate_code(problem_description)
    except Exception as e:
        raise ToolError(f"Failed to generate code: {e!s}") from e

    if response.get("error"):
        return ToolResult(content=[TextContent(type="text", text=f"Code generation failed: {response['error']}")])

    content = []
    if response.get("explanation"):
        content.append(TextContent(type="text", text=response["explanation"]))
    if response.get("code"):
        content.append(TextContent(type="text", text=f"```python\n{response['code']}\n```"))

    return ToolResult(content=content, structured_content=response)


@mcp.tool(
    name="execute_code",
    description=(
        "Execute Python code in a sandboxed environment with JAX (jnp), diffrax, equinox, "
        "and the ax_core.model_fitter library available. Code must call export(name, value) "
        "at least once to return results. Typically used to run code produced by generate_code, "
        "but also accepts hand-written or modified code."
    ),
    tags=["model-fitter", "execution", "sandbox"],
)
async def execute_code(
    code: Annotated[str, "Python code to execute. Must call export(name, value) to return results."],
) -> ToolResult:
    """Execute Python fitting code in the model fitter sandbox."""
    try:
        response = model_fitter_service.execute_code(code)
    except Exception as e:
        raise ToolError(f"Failed to execute code: {e!s}") from e

    if not response.get("success"):
        error_msg = response.get("error", "Unknown execution error")
        stdout = response.get("stdout", "")
        text = f"Execution failed: {error_msg}"
        if stdout:
            text += f"\n\nStdout:\n{stdout}"
        return ToolResult(content=[TextContent(type="text", text=text)])

    parts = []
    if response.get("result"):
        parts.append(TextContent(type="text", text=f"Result: {response['result']}"))
    if response.get("stdout"):
        parts.append(TextContent(type="text", text=f"Stdout:\n{response['stdout']}"))
    parts.append(TextContent(type="text", text=f"Execution time: {response.get('execution_time', 0):.3f}s"))

    return ToolResult(content=parts, structured_content=response)


def main():
    """Main entry point for the model fitter MCP server."""
    mcp.run(transport="stdio")
