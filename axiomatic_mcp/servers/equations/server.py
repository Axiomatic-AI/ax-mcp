from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.api_client import AxiomaticAPIClient
from ...shared.utils.file_utils import get_file_type
from ...shared.utils.prompt_utils import get_feedback_prompt

mcp = FastMCP(
    name="AxEquationExplorer Server",
    instructions="""This server provides tools to compose and analyze equations.
    """ + get_feedback_prompt("find_functional_form, check_equation"),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)


@mcp.tool(
    name="find_functional_form",
    description=(
        "Derive an expression of your interest given the information from the source documents "
        "and equations residing there. Provide description of the expression you want to compose."
    ),
    tags=["equations", "compose", "derive", "find", "function-finder"],
)
async def find_expression(
    document: Annotated[Path | str, "Either a file path to a PDF document or the document content as a string"],
    task: Annotated[str, "The task to be done for expression composition"],
) -> ToolResult:
    """If you have scientific text with equations, but you don't see the equation you're
    interested in then use this tool and simply say: 'Express the energy in terms of
    velocity and position', or something like that. The tool will return the desired expression
    together with sympy code that explains how it was derived."""

    with AxiomaticAPIClient() as client:  # ← Fixed: Use context manager
        if isinstance(document, Path) and get_file_type(str(document)) == "application/pdf":
            files = {"pdf_file": (document.name, document.read_bytes(), "application/pdf")}
            data = {"task": task}
            response = client.post("/equations/derive", data=data, files=files)
        elif isinstance(document, Path) and get_file_type(str(document)) in ["text/markdown", "text/plain", "text/html"]:
            data = {"markdown": document.read_text(encoding="utf-8"), "task": task}
            response = client.post("/equations/derive", data=data)
        elif isinstance(document, str):
            data = {"markdown": document, "task": task}
            response = client.post("/equations/derive", data=data)
        else:
            raise ToolError(
                f"Unsupported file type: {get_file_type(str(document)) if isinstance(document, Path) else 'string content'}. Supported types: pdf, markdown, plain text, html"
            )

    if isinstance(document, Path):
        code_file_path = document.parent / f"{document.stem}_code.py"
        explanation_file_path = document.parent / f"{document.stem}_explanation.md"
    else:
        code_file_path = Path.cwd() / "expression_code.py"
        explanation_file_path = Path.cwd() / "expression_explanation.md"

    with Path.open(code_file_path, "w", encoding="utf-8") as f:
        f.write(response.get("code", ""))

    with Path.open(explanation_file_path, "w", encoding="utf-8") as f:
        f.write(response.get("explanation", ""))

    return ToolResult(
        content=[
            TextContent(type="text", text=f"Explanation: {response.get('explanation', '')}"),
            TextContent(type="text", text=f"Code: {response.get('code', '')}"),
        ]
    )


@mcp.tool(
    name="check_equation",
    description=(
        "Ask the agent to check the correctness of the equation or correct potential errors. "
        "This tool validates equations and provides corrections if needed."
    ),
    tags=["equations", "check", "error-correction", "validate"],
)
async def check_equation(
    document: Annotated[Path | str, "Either a file path to a PDF document or the document content as a string"],
    task: Annotated[str, "The task to be done for expression correctness checking"],
) -> ToolResult:
    """If you have scientific text with equations, but you don't see the equation you're
    interested in then use this tool and simply say: 'Express the energy in terms of
    velocity and position', or something like that. The tool will return the desired expression
    together with sympy code that explains how it was derived."""

    with AxiomaticAPIClient() as client:  # ← Fixed: Use context manager
        if isinstance(document, Path) and get_file_type(str(document)) == "application/pdf":
            files = {"pdf_file": (document.name, document.read_bytes(), "application/pdf")}
            data = {"task": task}
            response = client.post("/equations/check", data=data, files=files)
        elif isinstance(document, Path) and get_file_type(str(document)) in ["text/markdown", "text/plain", "text/html"]:
            data = {"markdown": document.read_text(encoding="utf-8"), "task": task}
            response = client.post("/equations/check", data=data)
        elif isinstance(document, str):
            data = {"markdown": document, "task": task}
            response = client.post("/equations/check", data=data)
        else:
            raise ToolError(
                f"Unsupported file type: {get_file_type(str(document)) if isinstance(document, Path) else 'string content'}. Supported types: pdf, markdown, plain text, html"
            )

    if isinstance(document, Path):
        code_file_path = document.parent / f"{document.stem}_code.py"
        explanation_file_path = document.parent / f"{document.stem}_explanation.md"
    else:
        code_file_path = Path.cwd() / "expression_code.py"
        explanation_file_path = Path.cwd() / "expression_explanation.md"

    with Path.open(code_file_path, "w", encoding="utf-8") as f:
        f.write(response.get("code", ""))

    with Path.open(explanation_file_path, "w", encoding="utf-8") as f:
        f.write(response.get("explanation", ""))

    return ToolResult(
        content=[
            TextContent(type="text", text=f"Explanation: {response.get('explanation', '')}"),
            TextContent(type="text", text=f"Code: {response.get('code', '')}"),
        ]
    )
