from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.api_client import AxiomaticAPIClient
from ...shared.documents.pdf_to_markdown import pdf_to_markdown
from ...shared.utils.prompt_utils import get_feedback_prompt


async def _get_document_content(document: Path | str) -> str:
    """Helper function to extract document content from either a file path or direct content."""
    if isinstance(document, Path):
        if not document.exists():
            raise ValueError(f"File not found: {document}")

        if document.suffix.lower() == ".pdf":
            response = await pdf_to_markdown(document)
            return response.markdown
        elif document.suffix.lower() in [".md", ".txt"]:
            with Path.open(document, encoding="utf-8") as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file type: {document.suffix}. Supported types: .pdf, .md, .txt")

    if len(document) < 500 and "\n" not in document:
        potential_path = Path(document)
        if potential_path.exists():
            if potential_path.suffix.lower() == ".pdf":
                response = await pdf_to_markdown(potential_path)
                return response.markdown
            elif potential_path.suffix.lower() in [".md", ".txt"]:
                with Path.open(potential_path, encoding="utf-8") as f:
                    return f.read()

    return document


mcp = FastMCP(
    name="AxEquationExplorer Server",
    instructions="""This server provides tools to compose and analyze equations.
    """
    + get_feedback_prompt("find_functional_form, check_equation"),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)


@mcp.tool(
    name="find_functional_form",
    description=(
        "Compose an expression of your interest given the information from the source documents "
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
    try:
        doc_content = await _get_document_content(document)

        input_body = {"markdown": doc_content, "task": task}
        response = AxiomaticAPIClient().post("/equations/derive/markdown", data=input_body)

        code = response.get("composer_code", "")

        if not code:
            raise ToolError("No composer_code returned from service")

        code = response.get("composer_code", "")

        if isinstance(document, Path) or (isinstance(document, str) and Path(document).exists()):
            doc_path = Path(document)
            file_path = doc_path.parent / f"{doc_path.stem}_code.py"
        else:
            file_path = Path.cwd() / "expression_code.py"

        with Path.open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        return ToolResult(
            content=[
                TextContent(type="text", text=f"Comments: {response.get('comments', '')}"),
                TextContent(type="text", text=f"Code: {response.get('composer_code', '')}"),
            ]
        )

    except Exception as e:
        raise ToolError(f"Failed to analyze document: {e!s}") from e


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
    try:
        doc_content = await _get_document_content(document)
        input_body = {"markdown": doc_content, "task": task}
        # Note: Using the same endpoint for now, but this could be changed to a dedicated checking endpoint
        response = AxiomaticAPIClient().post("/equations/check/markdown", data=input_body)

        return ToolResult(
            content=[
                TextContent(type="text", text=f"Comments: {response.get('comments', '')}"),
                TextContent(type="text", text=f"Code: {response.get('composer_code', '')}"),
            ]
        )

    except Exception as e:
        raise ToolError(f"Failed to check equations in document: {e!s}") from e
