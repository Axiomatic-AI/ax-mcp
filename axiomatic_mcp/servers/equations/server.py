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

CRITICAL: For the derive_all_equations workflow, you MUST follow this exact pattern:

1. Call derive_all_equations_analyze
2. Show results to user and ASK: "Are you satisfied with this categorization, or would you like to make changes?"
3. Based on user response:
   - If user wants changes: call derive_all_equations_modify → show results → ASK AGAIN (repeat as needed)
   - If user approves: IMMEDIATELY call derive_all_equations_execute (don't ask again, just do it)
4. NEVER skip asking the user for approval after analyze/modify
5. ALWAYS execute automatically once user approves (this is the final step, no more modifications)

The modify tool is OPTIONAL and should only be called if user explicitly wants changes. Otherwise proceed directly to execute after user approval.
    """
    + get_feedback_prompt(
        "find_functional_form, check_equation, generate_derivation_graph, derive_all_equations_analyze, derive_all_equations_modify, derive_all_equations_execute"
    ),
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


@mcp.tool(
    name="derive_all_equations_analyze",
    description=(
        "Step 1: Analyzes a scientific document and categorizes equations. "
        "CRITICAL: After calling this, you MUST ask user if they approve or want changes. "
        "Do not proceed without explicit user approval."
    ),
    tags=["equations", "derive", "analyze", "categorize"],
)
async def derive_all_equations_analyze(
    document: Annotated[
        Path | str,
        "Either a file path to a PDF/markdown document or the document content as a string",
    ],
) -> ToolResult:
    """Step 1: Analyze and categorize equations.

    After calling this tool, you MUST:
    1. Show the results to the user
    2. Ask: "Are you satisfied with this categorization, or would you like to make changes?"
    3. Wait for user response before proceeding
    """
    try:
        doc_content = await _get_document_content(document)

        analysis_response = AxiomaticAPIClient().post(
            "/equations/derive-all/analyze",
            data={"markdown": doc_content},
        )

        eligible_equations = analysis_response.get("eligible_equations", [])
        not_eligible_equations = analysis_response.get("not_eligible_equations", [])
        summary = analysis_response.get("summary", "")

        # Format analysis results for display
        analysis_text = f"## Equation Analysis Complete\n\n{summary}\n\n"
        analysis_text += f"### ✅ ELIGIBLE FOR DERIVATION ({len(eligible_equations)} equations):\n\n"

        for i, eq in enumerate(eligible_equations, 1):
            analysis_text += f"{i}. {eq.get('equation', 'N/A')}\n"
            analysis_text += f"   Context: {eq.get('context', 'N/A')}\n"
            analysis_text += f"   Rationale: {eq.get('rationale', 'N/A')}\n\n"

        analysis_text += f"### ❌ NOT ELIGIBLE ({len(not_eligible_equations)} equations):\n\n"
        for i, eq in enumerate(not_eligible_equations, 1):
            analysis_text += f"{i}. {eq.get('equation', 'N/A')}\n"
            analysis_text += f"   Context: {eq.get('context', 'N/A')}\n"
            analysis_text += f"   Rationale: {eq.get('rationale', 'N/A')}\n\n"

        return ToolResult(content=[TextContent(type="text", text=analysis_text)])

    except Exception as e:
        raise ToolError(f"Failed to analyze equations: {e!s}") from e


@mcp.tool(
    name="derive_all_equations_modify",
    description=(
        "Step 2 (OPTIONAL): Modify categorization based on user instructions. "
        "CRITICAL: After calling this, you MUST ask user if they approve the changes or want more changes. "
        "Only call this if user explicitly requested modifications."
    ),
    tags=["equations", "derive", "modify", "categorize"],
)
async def derive_all_equations_modify(
    document: Annotated[
        Path | str,
        "The same document used in analyze step",
    ],
    user_instructions: Annotated[
        str,
        "Natural language instructions for modifying the categorization",
    ],
    eligible_equations: Annotated[
        list[dict],
        "Current list of eligible equations (from analyze or previous modify call)",
    ],
    not_eligible_equations: Annotated[
        list[dict],
        "Current list of not eligible equations (from analyze or previous modify call)",
    ],
) -> ToolResult:
    """Step 2 (OPTIONAL): Modify categorization based on user instructions.

    After calling this tool, you MUST:
    1. Show the updated results to the user
    2. Ask: "Are you satisfied with these changes, or would you like more modifications?"
    3. Wait for user response before proceeding
    """
    try:
        modify_response = AxiomaticAPIClient().post(
            "/equations/derive-all/modify-categorization",
            data={
                "eligible_equations": eligible_equations,
                "not_eligible_equations": not_eligible_equations,
                "user_instructions": user_instructions,
            },
        )

        updated_eligible = modify_response.get("eligible_equations", [])
        updated_not_eligible = modify_response.get("not_eligible_equations", [])
        summary = modify_response.get("summary", "")
        changes_made = modify_response.get("changes_made", [])

        # Format results
        result_text = f"## Categorization Modified\n\n{summary}\n\n"

        if changes_made:
            result_text += "**Changes made:**\n"
            for change in changes_made:
                result_text += f"- {change}\n"
            result_text += "\n"

        result_text += f"### ✅ ELIGIBLE FOR DERIVATION ({len(updated_eligible)} equations):\n\n"
        for i, eq in enumerate(updated_eligible, 1):
            result_text += f"{i}. {eq.get('equation', 'N/A')}\n"
            result_text += f"   Context: {eq.get('context', 'N/A')}\n"
            result_text += f"   Rationale: {eq.get('rationale', 'N/A')}\n\n"

        result_text += f"### ❌ NOT ELIGIBLE ({len(updated_not_eligible)} equations):\n\n"
        for i, eq in enumerate(updated_not_eligible, 1):
            result_text += f"{i}. {eq.get('equation', 'N/A')}\n"
            result_text += f"   Context: {eq.get('context', 'N/A')}\n"
            result_text += f"   Rationale: {eq.get('rationale', 'N/A')}\n\n"

        return ToolResult(content=[TextContent(type="text", text=result_text)])

    except Exception as e:
        raise ToolError(f"Failed to modify categorization: {e!s}") from e


@mcp.tool(
    name="derive_all_equations_execute",
    description=(
        "Step 3: Execute derivations after user approval. "
        "Call this IMMEDIATELY when user approves the categorization (don't ask again). "
        "This is the final step - takes 2-10 minutes, generates .py files."
    ),
    tags=["equations", "derive", "execute", "batch", "parallel"],
)
async def derive_all_equations_execute(
    document: Annotated[
        Path | str,
        "The same document used in analyze step",
    ],
    eligible_equations: Annotated[
        list[dict],
        "Final approved list of equations to derive (from analyze or modify step)",
    ],
    output_directory: Annotated[
        str | None,
        "Directory where the equation .py files will be saved. Defaults to current directory.",
    ] = None,
) -> ToolResult:
    """Step 3: Execute derivations (call immediately after user approves).

    IMPORTANT: This should be called automatically when the user approves the categorization.
    Do not ask the user again - just execute.

    This is a synchronous operation (2-10 minutes) that:
    1. Derives all equations in parallel batches
    2. Generates SymPy code files
    3. Returns success/failure summary
    """
    try:
        doc_content = await _get_document_content(document)

        equations_to_derive = [eq.get("equation") for eq in eligible_equations]

        if not equations_to_derive:
            return ToolResult(content=[TextContent(type="text", text="No eligible equations to derive.")])

        num_equations = len(equations_to_derive)
        estimated_minutes = max(2, (num_equations // 10) * 3)

        # Show progress message before starting
        progress_text = f"🚀 Deriving {num_equations} equations...\n"
        progress_text += f"⏳ Estimated time: {estimated_minutes}-{estimated_minutes + 2} minutes (processing in parallel batches)\n"
        progress_text += "⏳ Please wait...\n\n"

        # Call synchronous execute endpoint (will block until complete)
        execute_response = AxiomaticAPIClient().post(
            "/equations/derive-all/execute",
            data={"markdown": doc_content, "eligible_equations": equations_to_derive},
        )

        derivation_results = execute_response.get("derivation_results", [])
        total_equations = execute_response.get("total_equations", 0)
        successful = execute_response.get("successful_derivations", 0)
        failed = execute_response.get("failed_derivations", 0)

        # Save files
        output_dir = Path(output_directory) if output_directory else Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        failed_equations = []

        for i, result in enumerate(derivation_results, 1):
            if result.get("success"):
                equation = result.get("equation", "")
                comments = result.get("comments", "")
                code = result.get("composer_code", "")

                file_content = f'"""\nDerivation of: {equation}\n\n{comments}\n"""\n\n{code}'

                file_path = output_dir / f"equation_{i}.py"
                with Path.open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)

                saved_files.append(str(file_path))
            else:
                error_msg = result.get("error_message", "Unknown error")
                failed_equations.append(f"Equation {i} ({result.get('equation', 'N/A')}): {error_msg}")

        # Format results
        result_text = progress_text
        result_text += "✅ Derivation complete!\n\n"
        result_text += "## Summary\n\n"
        result_text += f"- **Total equations**: {total_equations}\n"
        result_text += f"- **✅ Successfully derived**: {successful}\n"
        result_text += f"- **❌ Failed**: {failed}\n\n"

        if saved_files:
            result_text += "### Successfully created files:\n\n"
            for file_path in saved_files:
                result_text += f"- [{Path(file_path).name}]({file_path})\n"
            result_text += "\n"

        if failed_equations:
            result_text += "### Failed derivations:\n\n"
            for failure in failed_equations:
                result_text += f"- {failure}\n"
            result_text += "\n"

        return ToolResult(content=[TextContent(type="text", text=result_text)])

    except Exception as e:
        raise ToolError(f"Failed to execute derivations: {e!s}") from e
