"""AxTidy3D MCP server — generate, estimate, and run Tidy3D FDTD/mode-solving simulations."""

from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .services.tidy3d_service import Tidy3DService

mcp = FastMCP(
    name="AxTidy3D Server",
    instructions="""This server generates and runs Tidy3D electromagnetic simulation code
    (FDTD, mode solving). Workflow: (1) generate_code to produce a script from a problem
    description; (2) execute_code to run it — local operations (e.g. ModeSolver) run for
    free and return results immediately, while cloud FDTD code that calls submit_to_cloud(sim)
    only uploads and estimates cost, returning a task_id and estimated_cost_flex_credits
    WITHOUT spending anything; (3) ALWAYS show the estimated cost to the user and get their
    explicit confirmation before calling start_simulation with that task_id — this is the
    only step that spends real Flex credits; (4) get_simulation_status to poll until done.
    Requires a Tidy3D API key linked to the caller's Axiomatic account before any cloud step.
    """ + get_feedback_prompt(["generate_code", "execute_code", "start_simulation", "get_simulation_status"]),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)

tidy3d_service = Tidy3DService()


@mcp.tool(
    name="generate_code",
    description=(
        "Generate Python code for a Tidy3D simulation (FDTD, mode solving) from a natural "
        "language problem description. Returns executable code and an explanation. The code "
        "must be run separately using execute_code. If a previous attempt failed, pass "
        "previous_code and previous_error so the generator can fix it instead of starting over."
    ),
    tags=["tidy3d", "fdtd", "code-generation"],
)
async def generate_code(
    problem_description: Annotated[str, "Natural language description of the simulation to build"],
    previous_code: Annotated[str | None, "The code from a prior failed attempt, if retrying"] = None,
    previous_error: Annotated[str | None, "The error message from the prior failed attempt, if retrying"] = None,
) -> ToolResult:
    """Generate Python code for a Tidy3D simulation."""
    try:
        response = tidy3d_service.generate_code(problem_description, previous_code, previous_error)
    except Exception as e:
        raise ToolError(f"Failed to generate Tidy3D code: {e!s}") from e

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
        "Execute Tidy3D code. Local operations (e.g. ModeSolver.solve()) run for free and "
        "return results synchronously via export(name, value). Code that calls "
        "submit_to_cloud(sim) instead uploads the simulation and returns a cost estimate "
        "(task_id, task_status='estimated', estimated_cost_flex_credits) WITHOUT starting "
        "the run — nothing is billed at this point. Show the estimated cost to the user and "
        "get their confirmation, then call start_simulation with the returned task_id to "
        "actually run it."
    ),
    tags=["tidy3d", "execution", "sandbox"],
)
async def execute_code(
    code: Annotated[str, "Tidy3D Python code to execute"],
) -> ToolResult:
    """Execute Tidy3D code (local run, or cloud upload + cost estimate)."""
    try:
        response = tidy3d_service.execute_code(code)
    except Exception as e:
        raise ToolError(f"Failed to execute Tidy3D code: {e!s}") from e

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
    if response.get("task_id"):
        cost = response.get("estimated_cost_flex_credits")
        parts.append(
            TextContent(
                type="text",
                text=(
                    f"Uploaded as task_id={response['task_id']} (status: {response.get('task_status')}). "
                    f"Estimated cost: {cost} Flex credits. NOT started yet — confirm with the user, then "
                    f"call start_simulation with this task_id to run it."
                ),
            )
        )
    if response.get("stdout"):
        parts.append(TextContent(type="text", text=f"Stdout:\n{response['stdout']}"))
    if response.get("execution_time") is not None:
        parts.append(TextContent(type="text", text=f"Execution time: {response['execution_time']:.3f}s"))

    return ToolResult(content=parts, structured_content=response)


@mcp.tool(
    name="start_simulation",
    description=(
        "Start a previously estimated Tidy3D cloud task. This is the ONLY step that spends "
        "real Flex credits — only call this after the estimated_cost_flex_credits from "
        "execute_code has been shown to and explicitly confirmed by the user. Use the task_id "
        "returned by execute_code (where task_status was 'estimated')."
    ),
    tags=["tidy3d", "execution", "cloud"],
)
async def start_simulation(
    task_id: Annotated[str, "The task_id returned by execute_code's cost estimate"],
    task_name: Annotated[str | None, "Optional display name for the task"] = None,
) -> ToolResult:
    """Start a previously estimated Tidy3D cloud simulation."""
    try:
        response = tidy3d_service.start_task(task_id, task_name)
    except Exception as e:
        raise ToolError(f"Failed to start Tidy3D simulation: {e!s}") from e

    return ToolResult(
        content=[
            TextContent(
                type="text",
                text=f"Task {response.get('task_id')} status: {response.get('task_status')}. Poll with get_simulation_status.",
            )
        ],
        structured_content=response,
    )


@mcp.tool(
    name="get_simulation_status",
    description="Poll the status of a running or completed Tidy3D cloud task, and its real cost once known.",
    tags=["tidy3d", "status", "cloud"],
)
async def get_simulation_status(
    task_id: Annotated[str, "The task_id to check"],
) -> ToolResult:
    """Poll the status of a Tidy3D cloud task."""
    try:
        response = tidy3d_service.get_task_status(task_id)
    except Exception as e:
        raise ToolError(f"Failed to get Tidy3D task status: {e!s}") from e

    cost = response.get("real_cost_flex_credits")
    text = f"Task {response.get('task_id')} status: {response.get('task_status')}"
    if cost is not None:
        text += f" (cost so far: {cost} Flex credits)"

    return ToolResult(content=[TextContent(type="text", text=text)], structured_content=response)
