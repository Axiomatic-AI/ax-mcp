import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context, FastMCP

if TYPE_CHECKING:
    from leanclient import LeanLSPClient
from mcp.server.fastmcp.utilities.logging import get_logger

from .lean_client import (
    lean_completions_impl,
    lean_declaration_file_impl,
    lean_diagnostic_messages_impl,
    lean_file_contents_impl,
    lean_goal_impl,
    lean_hover_info_impl,
    lean_multi_attempt_impl,
    lean_run_code_impl,
    lean_term_goal_impl,
)

logger = get_logger(__name__)


# Server Context
@dataclass
class AppContext:
    lean_project_path: str | None
    client: "LeanLSPClient | None"
    file_content_hashes: dict[str, str]
    rate_limit: dict[str, list[int]]


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    try:
        lean_project_path = os.environ.get("LEAN_PROJECT_PATH", "").strip()
        lean_project_path = None if not lean_project_path else str(Path(lean_project_path).resolve())

        context = AppContext(
            lean_project_path=lean_project_path,
            client=None,
            file_content_hashes={},
            rate_limit={
                "leansearch": [],
                "loogle": [],
                "lean_state_search": [],
                "hammer_premise": [],
            },
        )
        logger.info(f"Leanclient MCP server starting with project path: {lean_project_path}")
        yield context
    finally:
        logger.info("Closing Lean LSP client")
        ctx_obj = locals().get("context")
        if ctx_obj and ctx_obj.client:
            ctx_obj.client.close()


# Instructions
INSTRUCTIONS = """## General Rules
- All line and column numbers are 1-indexed (use lean_file_contents if unsure).
- Always analyze/search context before each file edit.
- This MCP does NOT make permanent file changes. Use other tools for editing.
- Work iteratively: Small steps, intermediate sorries, frequent checks.

## Key Tools
- lean_goal: Check proof state. USE OFTEN!
- lean_diagnostic_messages: Understand the current proof situation.
- lean_hover_info: Documentation about terms and lean syntax.
- lean_leansearch: Search theorems using natural language or Lean terms.
- lean_loogle: Search definitions and theorems by name, type, or subexpression.
- lean_state_search: Search theorems using goal-based search.
"""

# MCP Server Setup
mcp = FastMCP(
    name="Lean LSP",
    instructions=INSTRUCTIONS,
    dependencies=["leanclient"],
    lifespan=app_lifespan,
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


@mcp.tool("lean_goal")
def lean_goal(ctx: Context, file_path: str, line: int, column: int | None = None) -> str:
    """Get the proof goals (proof state) at a specific location in a Lean file.

    VERY USEFUL! Main tool to understand the proof state and its evolution!
    Returns "no goals" if solved.
    To see the goal at sorry, use the cursor before the "s".
    Avoid giving a column if unsure-default behavior works well.

    Args:
        file_path (str): Abs path to Lean file
        line (int): Line number (1-indexed)
        column (int, optional): Column number (1-indexed). Defaults to None => Both before and after the line.

    Returns:
        str: Goal(s) or error msg
    """
    return lean_goal_impl(ctx, file_path, line, column)


@mcp.tool("lean_term_goal")
def lean_term_goal(ctx: Context, file_path: str, line: int, column: int | None = None) -> str:
    """Get the expected type (term goal) at a specific location in a Lean file.

    Args:
        file_path (str): Abs path to Lean file
        line (int): Line number (1-indexed)
        column (int, optional): Column number (1-indexed). Defaults to None => end of line.

    Returns:
        str: Expected type or error msg
    """
    return lean_term_goal_impl(ctx, file_path, line, column)


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


@mcp.tool("lean_completions")
def lean_completions(ctx: Context, file_path: str, line: int, column: int, max_completions: int = 32) -> str:
    """Get code completions at a location in a Lean file.

    Only use this on INCOMPLETE lines/statements to check available identifiers and imports:
    - Dot Completion: Displays relevant identifiers after a dot (e.g., `Nat.`, `x.`, or `Nat.ad`).
    - Identifier Completion: Suggests matching identifiers after part of a name.
    - Import Completion: Lists importable files after `import` at the beginning of a file.

    Args:
        file_path (str): Abs path to Lean file
        line (int): Line number (1-indexed)
        column (int): Column number (1-indexed)
        max_completions (int, optional): Maximum number of completions to return. Defaults to 32

    Returns:
        str: List of possible completions or error msg
    """
    return lean_completions_impl(ctx, file_path, line, column, max_completions)


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


@mcp.tool("lean_multi_attempt")
def lean_multi_attempt(ctx: Context, file_path: str, line: int, snippets: list[str]) -> list[str] | str:
    """Try multiple Lean code snippets at a line and get the goal state and diagnostics for each.

    Use to compare tactics or approaches.
    Use rarely-prefer direct file edits to keep users involved.
    For a single snippet, edit the file and run `lean_diagnostic_messages` instead.

    Note:
        Only single-line, fully-indented snippets are supported.
        Avoid comments for best results.

    Args:
        file_path (str): Abs path to Lean file
        line (int): Line number (1-indexed)
        snippets (List[str]): List of snippets (3+ are recommended)

    Returns:
        List[str] | str: Diagnostics and goal states or error msg
    """
    return lean_multi_attempt_impl(ctx, file_path, line, snippets)


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


if __name__ == "__main__":
    mcp.run()
