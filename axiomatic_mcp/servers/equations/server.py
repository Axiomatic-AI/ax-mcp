import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .services.equations_service import EquationsService

DocumentFields = tuple[str | None, tuple[str, bytes, str] | None]


def _resolve_path(document: Path | str) -> Path | None:
    """Return a Path if the document refers to an existing file, otherwise None."""
    if isinstance(document, Path):
        if not document.exists():
            raise ValueError(f"File not found: {document}")
        return document

    if len(document) < 500 and "\n" not in document:
        potential_path = Path(document)
        if potential_path.exists():
            return potential_path

    return None


async def _resolve_document(document: Path | str) -> DocumentFields:
    """Resolve a document into either markdown content or a PDF upload.

    Returns a (markdown, pdf_file) tuple where exactly one element is set.
    PDFs are uploaded directly so the API performs the parsing.
    """
    path = _resolve_path(document)

    if path is None:
        return str(document), None

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        content = await asyncio.to_thread(path.read_bytes)
        return None, (path.name, content, "application/pdf")
    elif suffix in [".md", ".txt"]:
        markdown = await asyncio.to_thread(path.read_text, encoding="utf-8")
        return markdown, None
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}. Supported types: .pdf, .md, .txt")


def _write_code_file(document: Path | str, code: str) -> None:
    """Persist the returned code next to the source document, or in the CWD."""
    if isinstance(document, Path) or (isinstance(document, str) and Path(document).exists()):
        doc_path = Path(document)
        file_path = doc_path.parent / f"{doc_path.stem}_code.py"
    else:
        file_path = Path.cwd() / "expression_code.py"

    with Path.open(file_path, "w", encoding="utf-8") as f:
        f.write(code)


async def _run_equation_tool(
    api_call: Callable[..., dict[str, Any]],
    document: Path | str,
    task: str,
    error_msg: str,
) -> ToolResult:
    """Shared flow for the equation tools: resolve input, call the API, persist and return."""
    try:
        markdown, pdf_file = await _resolve_document(document)
        response = api_call(task=task, markdown=markdown, pdf_file=pdf_file)

        _write_code_file(document, response.get("code", ""))

        return ToolResult(
            content=[
                TextContent(type="text", text=f"Explanation: {response.get('explanation', '')}"),
                TextContent(type="text", text=f"Code: {response.get('code', '')}"),
            ]
        )

    except Exception as e:
        raise ToolError(f"{error_msg}: {e!s}") from e


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
    return await _run_equation_tool(
        EquationsService().derive,
        document,
        task,
        "Failed to derive the equation in the document",
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
    task: Annotated[str, "The task to be done for equation checking (e.g., 'check if E=mc² is correct')"],
) -> ToolResult:
    """Use this tool to validate equations or check for errors in mathematical expressions.
    For example: 'Check if the equation F = ma is dimensionally consistent' or
    'Verify the correctness of the Maxwell equations in the document'."""
    return await _run_equation_tool(
        EquationsService().check,
        document,
        task,
        "Failed to check equations in document",
    )
