from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .services.argmin_service import ArgminService

mcp = FastMCP(
    name="AxArgmin Server",
    instructions="""This server provides tools for numerical optimization, rootfinding, ODE simulation, and optimal control
    using the argmin library. Use generate_code to produce executable code from a problem description,
    then execute_code to run it in a sandboxed environment.
    """ + get_feedback_prompt(["generate_code", "execute_code"]),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)

argmin_service = ArgminService()


@mcp.tool(
    name="generate_code",
    description=(
        "Generate Python code to solve a numerical problem using the argmin library. "
        "Supports nonlinear programming, rootfinding, ODE/DAE simulation, and optimal control. "
        "Returns executable code and an explanation of the approach. "
        "The code must be executed separately using the execute_code tool."
    ),
    tags=["argmin", "optimization", "code-generation"],
)
async def generate_code(
    problem_description: Annotated[str, "Natural language or mathematical description of the problem"],
    problem_type: Annotated[
        str,
        "Problem type: 'nonlinear_program' (minimize f(x) s.t. constraints), "
        "'nonlinear_equations' (solve F(x)=0, rootfinding), "
        "'initial_value_problem' (integrate dx/dt=f(x,t), ODE/DAE), "
        "or 'optimal_control' (dynamic optimization over time)",
    ],
) -> ToolResult:
    """Generate Python code for a numerical problem using the argmin library."""
    valid_types = {"nonlinear_program", "nonlinear_equations", "initial_value_problem", "optimal_control"}
    if problem_type not in valid_types:
        raise ToolError(f"Invalid problem_type '{problem_type}'. Must be one of: {', '.join(sorted(valid_types))}")

    try:
        response = argmin_service.generate_code(problem_description, problem_type)
    except Exception as e:
        raise ToolError(f"Failed to generate code: {e!s}") from e

    if response.get("error"):
        return ToolResult(content=[TextContent(type="text", text=f"Code generation failed: {response['error']}")])

    content = []
    if response.get("explanation"):
        content.append(TextContent(type="text", text=response["explanation"]))
    if response.get("code"):
        content.append(TextContent(type="text", text=f"```python\n{response['code']}\n```"))

    return ToolResult(
        content=content,
        structured_content=response,
    )


@mcp.tool(
    name="execute_code",
    description=(
        "Execute Python code in a sandboxed environment with numpy, math, and the ax_core.argmin "
        "numerical library available. Code must call export(name, value) at least once to return results. "
        "Typically used to run code produced by the generate_code tool, but also accepts hand-written or modified code."
    ),
    tags=["argmin", "execution", "sandbox"],
)
async def execute_code(
    code: Annotated[str, "Python code to execute. Must call export(name, value) to return results."],
) -> ToolResult:
    """Execute Python code in the argmin sandbox."""
    try:
        response = argmin_service.execute_code(code)
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

    return ToolResult(
        content=parts,
        structured_content=response,
    )
