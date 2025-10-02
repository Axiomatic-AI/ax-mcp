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


async def _get_python_code(code_input: Path | str) -> tuple[str, Path | None]:
    """Helper function to extract Python code from either a file path or direct string.

    Returns:
        tuple: (code_content, file_path if input was a file, otherwise None)
    """
    if isinstance(code_input, Path):
        if not code_input.exists():
            raise ValueError(f"File not found: {code_input}")

        if code_input.suffix.lower() != ".py":
            raise ValueError(f"Unsupported file type: {code_input.suffix}. Only .py files are supported")

        with Path.open(code_input, encoding="utf-8") as f:
            return f.read(), code_input

    # Check if it's a short string that might be a file path
    if len(code_input) < 500 and "\n" not in code_input:
        potential_path = Path(code_input)
        if potential_path.exists() and potential_path.suffix.lower() == ".py":
            with Path.open(potential_path, encoding="utf-8") as f:
                return f.read(), potential_path

    # It's direct code content
    return code_input, None


mcp = FastMCP(
    name="AxEquationExplorer Server",
    instructions="""This server provides tools to compose and analyze equations.
    """
    + get_feedback_prompt("find_functional_form, check_equation, generate_derivation_graph"),
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
    document: Annotated[
        Path | str,
        "Either a file path to a PDF document or the document content as a string",
    ],
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
    document: Annotated[
        Path | str,
        "Either a file path to a PDF document or the document content as a string",
    ],
    task: Annotated[
        str,
        "The task to be done for equation checking (e.g., 'check if E=mc² is correct')",
    ],
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


@mcp.tool(
    name="generate_derivation_graph",
    description=(
        "Generates a Mermaid flowchart representing the mathematical derivation steps in SymPy code. "
        "Analyzes the provided SymPy code and creates a visual flowchart showing the derivation flow, "
        "intermediate calculations, and dependencies between steps."
    ),
    tags=["equations", "derivation", "graph", "flowchart", "visualization", "sympy"],
)
async def generate_derivation_graph(
    sympy_code: Annotated[
        Path | str,
        "Either a file path to a Python file containing SymPy code or the SymPy code as a string",
    ],
    system_prompt: Annotated[
        str | None,
        "Optional system prompt to guide the graph generation. If not provided, a default prompt will be used.",
    ] = None,
) -> ToolResult:
    """Use this tool to visualize the derivation steps in SymPy code as a Mermaid flowchart.

    This is particularly useful for:
    - Understanding complex mathematical derivations
    - Visualizing the flow from input variables to final results
    - Identifying dependencies between intermediate calculations
    - Creating documentation of derivation steps

    Example usage:
    - "Create a flowchart showing the derivation steps in this Euler-Lagrange code"
    - "Visualize how the Maxwell equations are derived in this SymPy script"
    - "Generate a graph showing the dependencies in this quantum mechanics derivation"

    The tool returns a Mermaid flowchart text that can be rendered in Markdown or visualization tools.
    """
    try:
        code_content, original_file_path = await _get_python_code(sympy_code)

        # Use default system prompt if not provided
        # TODO fix system_prompt handling: should already be used in core/services so this one is not used
        if not system_prompt:
            system_prompt = (
                "You are an expert in analyzing SymPy code and creating Mermaid flowcharts. "
                "Analyze the provided SymPy derivation code and create a Mermaid flowchart that shows:\n"
                "1. The main steps in the mathematical derivation\n"
                "2. The flow from input variables to the final result\n"
                "3. Key intermediate calculations\n"
                "4. Dependencies between steps\n\n"
                "Output a valid Mermaid flowchart using the 'flowchart TD' syntax."
            )

        # Prepare the request data as form data (not JSON)
        # The backend expects multipart/form-data with Form() fields
        # We need to use files parameter to trigger multipart/form-data encoding
        form_data = {
            "system_prompt": (None, system_prompt),
            "sympy_code": (None, code_content),
        }

        # Call the API endpoint - using files parameter ensures multipart/form-data
        response = AxiomaticAPIClient().post(
            "/equations/compose/derivation-graph",
            files=form_data,  # Send as files to ensure multipart/form-data encoding
        )

        mermaid_text = response.get("mermaid_text", "")
        metadata = response.get("metadata")

        if not mermaid_text:
            raise ToolError("No mermaid_text returned from service")

        # Save the Mermaid output to a file
        if original_file_path:
            output_path = original_file_path.parent / f"{original_file_path.stem}_derivation.mmd"
        else:
            output_path = Path.cwd() / "derivation_graph.mmd"

        with Path.open(output_path, "w", encoding="utf-8") as f:
            f.write(mermaid_text)

        # Prepare result content
        # Check if mermaid_text already has code fences
        if mermaid_text.strip().startswith("```"):
            # Already wrapped, don't add more backticks
            mermaid_display = f"\nMermaid Flowchart:\n{mermaid_text}"
        else:
            # Not wrapped, add mermaid code fence
            mermaid_display = f"\nMermaid Flowchart:\n```mermaid\n{mermaid_text}\n```"

        result_content = [
            TextContent(type="text", text=f"Mermaid flowchart saved to: {output_path}"),
            TextContent(type="text", text=mermaid_display),
        ]

        if metadata:
            result_content.append(TextContent(type="text", text=f"\nMetadata: {metadata}"))

        return ToolResult(content=result_content)

    except Exception as e:
        raise ToolError(f"Failed to generate derivation graph: {e!s}") from e
