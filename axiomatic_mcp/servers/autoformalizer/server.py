import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.utilities.logging import get_logger

if TYPE_CHECKING:
    from leanclient import LeanLSPClient

from ...shared import AxiomaticAPIClient
from ..leanclient.lean_client import (
    lean_declaration_file_impl,
    lean_diagnostic_messages_impl,
    lean_file_contents_impl,
    lean_hover_info_impl,
    lean_run_code_impl,
)

logger = get_logger(__name__)


# Server Context
@dataclass
class AppContext:
    lean_project_path: str | None
    client: "LeanLSPClient | None"
    file_content_hashes: dict[str, str]


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    try:
        lean_project_path = os.environ.get("LEAN_PROJECT_PATH", "").strip()
        if not lean_project_path:
            lean_project_path = None
        else:
            lean_project_path = os.path.abspath(lean_project_path)

        context = AppContext(
            lean_project_path=lean_project_path,
            client=None,
            file_content_hashes={},
        )
        logger.info(f"Autoformalizer MCP server starting with project path: {lean_project_path}")
        yield context
    finally:
        logger.info("Closing Lean LSP client")
        if context.client:
            context.client.close()


SYSTEM_PROMPT = """
You are an expert Lean 4 theorem formalizer. Convert mathematical statements from PDFs into clean, syntactically correct Lean 4 theorem declarations.

## CRITICAL REQUIREMENTS (MUST FOLLOW EXACTLY):

### 1. IMPORTS - MANDATORY FORMAT:
- ONLY use: `import Mathlib`
- NEVER use specific imports like `import Mathlib.FieldTheory.Finite.Basic`
- NEVER use multiple import lines
- VIOLATION = IMMEDIATE FAILURE

### 2. THEOREM STRUCTURE - MANDATORY FORMAT:
- ALL theorems MUST end with: `:= by sorry`
- NEVER use tactics like `constructor`, `intro`, `rw`, `simp` except in proof sketch comments
- VIOLATION = IMMEDIATE FAILURE if not ending with `sorry`

### 3. FORMALIZATION SCOPE - WHAT TO DO:
- IF file is PDF: Extract content using document_to_markdown tool
- IF file is markdown: Read directly with standard file tools
- Identify main theorems, propositions, lemmas from extracted content
- Formalize ONLY the statements as clean theorem declarations
- Use standard Mathlib types and naming conventions
- Include necessary hypotheses as function parameters

### 4. FORMALIZATION SCOPE - WHAT NOT TO DO:
- DO NOT write any proofs (all steps must end with `sorry`)
- DO NOT create helper lemmas unless they appear in the source
- DO NOT add computational examples or verification code
- DO NOT create complex type hierarchies or abstract frameworks
- DO NOT use `sorry` except in the final position

### 5. CODE QUALITY REQUIREMENTS:
- Must compile without syntax errors
- Use clean, readable variable names
- Follow Mathlib naming conventions exactly
- Keep definitions minimal and focused
- Test with lean_diagnostic_messages before completion

### 6. OUTPUT STRUCTURE:
- Single .lean file with clean formalization
- Brief comment explaining the source theorem
- Theorem statements with optional proof sketches using `have` steps
- Verify compilation with Lean tools

## Available Tools:
- document_to_markdown: Extract text from PDF
- lean_file_contents: Read Lean files with line numbers
- lean_diagnostic_messages: Check for compilation errors (REQUIRED)
- lean_hover_info: Get symbol documentation
- lean_run_code: Test small code snippets (use sparingly)

## Success Criteria:
1. PDF or MARKDOWN content successfully extracted and understood
2. Main mathematical statements identified correctly 
3. Clean Lean 4 code with only `import Mathlib`
4. All theorems end with `:= by sorry`
5. Zero compilation errors via lean_diagnostic_messages
6. Minimal, focused formalization without extra complexity
"""

mcp = FastMCP(
    name="Autoformalizer",
    instructions=SYSTEM_PROMPT,
    dependencies=["leanclient"],
    lifespan=app_lifespan,
)


# Document Parsing Tools
@mcp.tool(
    name="document_to_markdown",
    description="Convert a PDF document to markdown and save to file using Axiomatic's advanced OCR.",
)
async def document_to_markdown(
    file_path: Annotated[Path, "Abs path to PDF file"],
) -> Annotated[str, "Markdown content of the document"]:
    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    file_content = file_path.read_bytes()
    files = {"file": (file_path.name, file_content, "application/pdf")}
    data = {"method": "mistral", "ocr": False, "layout_model": "doclayout_yolo"}

    response = AxiomaticAPIClient().post("/document/parse", files=files, data=data)

    # Save to file automatically
    output_path = file_path.with_suffix(".md")
    output_path.write_text(response["markdown"], encoding="utf-8")

    return f"Saved to {output_path}"


# LEAN CLIENT TOOLS
@mcp.tool("lean_file_contents")
def lean_file_contents(ctx: Context, file_path: str, annotate_lines: bool = True) -> str:
    """Get the text contents of a Lean file, optionally with line numbers.

    Args:
        file_path (str): Abs path to Lean file
        annotate_lines (bool, optional): Annotate lines with line numbers. Defaults to True.

    Returns:
        str: File content or error msg
    """
    return lean_file_contents_impl(ctx, file_path, annotate_lines)


@mcp.tool("lean_diagnostic_messages")
def lean_diagnostic_messages(ctx: Context, file_path: str) -> list[str] | str:
    """Get all diagnostic msgs (errors, warnings, infos) for a Lean file.

    "no goals to be solved" means code may need removal.

    Args:
        file_path (str): Abs path to Lean file

    Returns:
        List[str] | str: Diagnostic msgs or error msg
    """
    return lean_diagnostic_messages_impl(ctx, file_path)


@mcp.tool("lean_hover_info")
def lean_hover_info(ctx: Context, file_path: str, line: int, column: int) -> str:
    """Get hover info (docs for syntax, variables, functions, etc.) at a specific location in a Lean file.

    Args:
        file_path (str): Abs path to Lean file
        line (int): Line number (1-indexed)
        column (int): Column number (1-indexed). Make sure to use the start or within the term, not the end.

    Returns:
        str: Hover info or error msg
    """
    return lean_hover_info_impl(ctx, file_path, line, column)


@mcp.tool("lean_declaration_file")
def lean_declaration_file(ctx: Context, file_path: str, symbol: str) -> str:
    """Get the file contents where a symbol/lemma/class/structure is declared.

    Note:
        Symbol must be present in the file! Add if necessary!
        Lean files can be large, use `lean_hover_info` before this tool.

    Args:
        file_path (str): Abs path to Lean file
        symbol (str): Symbol to look up the declaration for. Case sensitive!

    Returns:
        str: File contents or error msg
    """
    return lean_declaration_file_impl(ctx, file_path, symbol)


@mcp.tool("lean_run_code")
def lean_run_code(ctx: Context, code: str) -> list[str] | str:
    """Run a complete, self-contained code snippet and return diagnostics.

    Has to include all imports and definitions!
    Only use for testing outside open files! Keep the user in the loop by editing files instead.

    Args:
        code (str): Code snippet

    Returns:
        List[str] | str: Diagnostics msgs or error msg
    """
    return lean_run_code_impl(ctx, code)
