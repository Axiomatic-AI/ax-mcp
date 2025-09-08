from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from axiomatic_mcp.shared.documents.pdf_to_markdown import pdf_to_markdown

from ...shared import AxiomaticAPIClient


async def _get_document_content(document: Path | str) -> str:
    """Helper function to extract document content from either a file path or direct content."""
    if isinstance(document, Path):
        if document.exists() and document.suffix.lower() == ".pdf":
            response = await pdf_to_markdown(document)
            return response.markdown
        else:
            raise ValueError(f"PDF file not found or invalid: {document}")

    potential_path = Path(document)
    if potential_path.exists() and potential_path.suffix.lower() == ".pdf":
        response = await pdf_to_markdown(potential_path)
        return response.markdown
    else:
        return document


mcp = FastMCP(
    name="AxEquationExplorer Server",
    instructions="""This server provides tools to compose and analyze equations.""",
    version="0.0.1",
)


@mcp.tool(
    name="function_finder",
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
        response = AxiomaticAPIClient().post("/document/expression/compose/markdown", data=input_body)

        code = response.get("composition_code", "")

        if not code:
            raise ToolError("No composition_code returned from service")

        code = response.get("composition_code", "")

        if isinstance(document, Path) or (isinstance(document, str) and Path(document).exists()):
            doc_path = Path(document)
            file_path = doc_path.parent / f"{doc_path.stem}_code.py"
        else:
            file_path = Path.cwd() / "expression_code.py"

        with Path.open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        return ToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Generated expression composition for: {file_path}\n\n```python\n{code}\n```",
                )
            ],
            structured_content={"result": {"status": "success", "path": str(file_path), "message": f"Equation code written to {file_path}"}},
        )

    except Exception as e:
        raise ToolError(f"Failed to analyze document: {e!s}") from e


@mcp.tool(
    name="equation_checker",
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
        response = AxiomaticAPIClient().post("/document/expression/compose/markdown", data=input_body)

        return ToolResult(
            content=[
                TextContent(type="text", text=f"Validation Results: {response.get('validation_results', response.get('comments', ''))}"),
                TextContent(type="text", text=f"Corrections: {response.get('corrections', response.get('composition_code', ''))}"),
            ]
        )

    except Exception as e:
        raise ToolError(f"Failed to check equations in document: {e!s}") from e
