from fastmcp import FastMCP
from mcp.server.fastmcp import Context

from ..leanclient.lean_client import (
    lean_declaration_file_impl,
    lean_diagnostic_messages_impl,
    lean_file_contents_impl,
    lean_hover_info_impl,
    lean_run_code_impl,
)

mcp = FastMCP(
    name="Autoformalizer",
    instructions="""You are an expert Lean 4 theorem formalizer. Convert natural language
mathematical statements into syntactically correct Lean 4 theorem declarations.

FORMALIZATION RULES:
- Use the axiomatic API 
- Use proper Lean 4 and Mathlib syntax
- Follow current Mathlib naming conventions
- USE import Mathlib and DO NOT USE specific imports such as import Mathlib.LinearAlgebra
- Include necessary hypotheses as parameters
- End all theorems and statements with := by sorry
- DO NOT PROVE THEOREMS.
""",
    version="0.0.1",
)


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
