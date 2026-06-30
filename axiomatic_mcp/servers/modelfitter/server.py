"""AxModelFitter server — generate_code / execute_code pattern."""

from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .data_inlining import DataInliningError, preview_table
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
        "but also accepts hand-written or modified code.\n\n"
        "Optionally pass data_file (a local .csv or .json path) to inline tabular data: the "
        "server reads it locally and injects `data`, a dict mapping each column name to a 1-D "
        "numpy float array (access as data['col']). Use `columns` to inline only a subset; call "
        "preview_data first to see the available columns. Intended for small datasets."
    ),
    tags=["model-fitter", "execution", "sandbox"],
)
async def execute_code(
    code: Annotated[str, "Python code to execute. Must call export(name, value) to return results."],
    data_file: Annotated[
        str | None,
        "Optional local .csv/.json path. Columns are inlined as a numpy dict `data` (data['col']).",
    ] = None,
    columns: Annotated[
        list[str] | None,
        "Optional subset of columns to inline (default: all columns).",
    ] = None,
) -> ToolResult:
    """Execute Python fitting code in the model fitter sandbox."""
    try:
        response = model_fitter_service.execute_code(code, data_file=data_file, columns=columns)
    except DataInliningError as e:
        raise ToolError(f"Data file error: {e!s}") from e
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


@mcp.tool(
    name="preview_data",
    description=(
        "Preview a local .csv or .json data file before fitting: returns its column "
        "names, per-column dtypes, and the first n_rows as sample records. Use this to "
        "decide which columns to pass as `columns` to execute_code. Reads only the head "
        "of the file, so it is cheap on large files."
    ),
    tags=["model-fitter", "data", "preview"],
)
async def preview_data(
    data_file: Annotated[str, "Local .csv or .json path to preview."],
    n_rows: Annotated[int, "Number of sample rows to return (default 20)."] = 20,
) -> ToolResult:
    """Return schema + head for a local data file."""
    try:
        info = preview_table(data_file, n_rows=n_rows)
    except DataInliningError as e:
        raise ToolError(f"Data file error: {e!s}") from e

    summary = "Columns: " + ", ".join(f"{c} ({info['dtypes'][c]})" for c in info["columns"])
    return ToolResult(
        content=[TextContent(type="text", text=summary)],
        structured_content=info,
    )


def main():
    """Main entry point for the model fitter MCP server."""
    mcp.run(transport="stdio")
