"""Main Lean Tools MCP Server that registers all tools."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from mcp.server.fastmcp import Context, FastMCP

if TYPE_CHECKING:
    from leanclient import LeanLSPClient
from mcp.server.fastmcp.utilities.logging import get_logger

from .lean_client import (
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
        if not lean_project_path:
            lean_project_path = None
        else:
            lean_project_path = os.path.abspath(lean_project_path)

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
        if context.client:
            context.client.close()


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
mcp_kwargs = dict(name="Lean LSP", instructions=INSTRUCTIONS, dependencies=["leanclient"], lifespan=app_lifespan)

# auth_token = os.environ.get("LEAN_LSP_MCP_TOKEN")
# if auth_token:
#     mcp_kwargs["auth"] = AuthSettings(
#         type="optional",
#         issuer_url="http://localhost/dummy-issuer",
#         resource_server_url="http://localhost/dummy-resource",
#     )
#     mcp_kwargs["token_verifier"] = OptionalTokenVerifier(auth_token)

mcp = FastMCP(**mcp_kwargs)


# Rate limiting decorator
# def rate_limited(category: str, max_requests: int, per_seconds: int):
#     def decorator(func):
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             rate_limit = kwargs["ctx"].request_context.lifespan_context.rate_limit
#             current_time = int(time.time())
#             rate_limit[category] = [timestamp for timestamp in rate_limit[category] if timestamp > current_time - per_seconds]
#             if len(rate_limit[category]) >= max_requests:
#                 return f"Tool limit exceeded: {max_requests} requests per {per_seconds} s. Try again later."
#             rate_limit[category].append(current_time)
#             return func(*args, **kwargs)

#         wrapper.__doc__ = f"Limit: {max_requests}req/{per_seconds}s. " + (wrapper.__doc__ or "")
#         return wrapper

#     return decorator


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


# @mcp.tool("lean_completions")
# def lean_completions(ctx: Context, file_path: str, line: int, column: int, max_completions: int = 32) -> str:
#     """Get code completions at a location in a Lean file.

#     Only use this on INCOMPLETE lines/statements to check available identifiers and imports:
#     - Dot Completion: Displays relevant identifiers after a dot (e.g., `Nat.`, `x.`, or `Nat.ad`).
#     - Identifier Completion: Suggests matching identifiers after part of a name.
#     - Import Completion: Lists importable files after `import` at the beginning of a file.

#     Args:
#         file_path (str): Abs path to Lean file
#         line (int): Line number (1-indexed)
#         column (int): Column number (1-indexed)
#         max_completions (int, optional): Maximum number of completions to return. Defaults to 32

#     Returns:
#         str: List of possible completions or error msg
#     """
#     return lean_completions_impl(ctx, file_path, line, column, max_completions)


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


# LEAN SYSTEM TOOLS

# @mcp.tool("lean_build")
# def lean_build(ctx: Context, lean_project_path: str = None, clean: bool = False) -> str:
#     """Build the Lean project and restart the LSP Server.

#     Use only if needed (e.g. new imports).

#     Args:
#         lean_project_path (str, optional): Path to the Lean project. If not provided, it will be inferred from previous tool calls.
#         clean (bool, optional): Run `lake clean` before building. Attention: Only use if it is really necessary! It can take a long time! Defaults to False.

#     Returns:
#         str: Build output or error msg
#     """
#     return lean_build_impl(ctx, lean_project_path, clean)


# WEB SEARCH TOOLS

# @mcp.tool("lean_leansearch")
# @rate_limited("leansearch", max_requests=3, per_seconds=30)
# def lean_leansearch(ctx: Context, query: str, num_results: int = 5) -> list[dict] | str:
#     """Limit: 3req/30s. Search for Lean theorems, definitions, and tactics using leansearch.net.

#     Query patterns:
#       - Natural language: "If there exist injective maps of sets from A to B and from B to A, then there exists a bijective map between A and B."
#       - Mixed natural/Lean: "natural numbers. from: n < m, to: n + 1 < m + 1", "n + 1 <= m if n < m"
#       - Concept names: "Cauchy Schwarz"
#       - Lean identifiers: "List.sum", "Finset induction"
#       - Lean term: "{f : A → B} {g : B → A} (hf : Injective f) (hg : Injective g) : ∃ h, Bijective h"

#     Args:
#         query (str): Search query
#         num_results (int, optional): Max results. Defaults to 5.

#     Returns:
#         List[Dict] | str: Search results or error msg
#     """
#     return lean_leansearch_impl(ctx, query, num_results)


# @mcp.tool("lean_loogle")
# @rate_limited("loogle", max_requests=3, per_seconds=30)
# def lean_loogle(ctx: Context, query: str, num_results: int = 8) -> list[dict] | str:
#     """Limit: 3req/30s. Search for definitions and theorems using loogle.

#     Query patterns:
#       - By constant: Real.sin  # finds lemmas mentioning Real.sin
#       - By lemma name: "differ"  # finds lemmas with "differ" in the name
#       - By subexpression: _ * (_ ^ _)  # finds lemmas with a product and power
#       - Non-linear: Real.sqrt ?a * Real.sqrt ?a
#       - By type shape: (?a -> ?b) -> List ?a -> List ?b
#       - By conclusion: |- tsum _ = _ * tsum _
#       - By conclusion w/hyps: |- _ < _ → tsum _ < tsum _

#     Args:
#         query (str): Search query
#         num_results (int, optional): Max results. Defaults to 8.

#     Returns:
#         List[dict] | str: Search results or error msg
#     """
#     return lean_loogle_impl(ctx, query, num_results)


# @mcp.tool("lean_state_search")
# @rate_limited("lean_state_search", max_requests=3, per_seconds=30)
# def lean_state_search(ctx: Context, file_path: str, line: int, column: int, num_results: int = 5) -> list | str:
#     """Limit: 3req/30s. Search for theorems based on proof state using premise-search.com.

#     Only uses first goal if multiple.

#     Args:
#         file_path (str): Abs path to Lean file
#         line (int): Line number (1-indexed)
#         column (int): Column number (1-indexed)
#         num_results (int, optional): Max results. Defaults to 5.

#     Returns:
#         List | str: Search results or error msg
#     """
#     return lean_state_search_impl(ctx, file_path, line, column, num_results)


# @mcp.tool("lean_hammer_premise")
# @rate_limited("hammer_premise", max_requests=3, per_seconds=30)
# def lean_hammer_premise(ctx: Context, file_path: str, line: int, column: int, num_results: int = 32) -> list[str] | str:
#     """Limit: 3req/30s. Search for premises based on proof state using the lean hammer premise search.

#     Args:
#         file_path (str): Abs path to Lean file
#         line (int): Line number (1-indexed)
#         column (int): Column number (1-indexed)
#         num_results (int, optional): Max results. Defaults to 32.

#     Returns:
#         List[str] | str: List of relevant premises or error message
#     """
#     return lean_hammer_premise_impl(ctx, file_path, line, column, num_results)


def main():
    """Main entry point for the leanclient server."""
    mcp.run()


if __name__ == "__main__":
    main()
