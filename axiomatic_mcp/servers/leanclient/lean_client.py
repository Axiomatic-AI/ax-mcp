import contextlib
import re
import subprocess
from pathlib import Path

from leanclient import DocumentContentChange, LeanLSPClient
from mcp.server.fastmcp import Context
from mcp.server.fastmcp.utilities.logging import get_logger

from .utils import (
    OutputCapture,
    StdoutToStderr,
    extract_range,
    filter_diagnostics_by_position,
    find_start_position,
    format_diagnostics,
    format_goal,
    format_line,
    get_file_contents,
    get_relative_file_path,
    valid_lean_project_path,
)

logger = get_logger(__name__)


def startup_client(ctx: Context):
    """Initialize the Lean LSP client if not already set up."""
    lean_project_path = ctx.request_context.lifespan_context.lean_project_path
    if lean_project_path is None:
        raise ValueError("lean project path is not set.")

    # Check if already correct client
    client: LeanLSPClient | None = ctx.request_context.lifespan_context.client

    if client is not None:
        if client.project_path == lean_project_path:
            return
        client.close()
        ctx.request_context.lifespan_context.file_content_hashes.clear()

    with StdoutToStderr():
        try:
            client = LeanLSPClient(lean_project_path, initial_build=True, print_warnings=False)
            logger.info(f"Connected to Lean language server at {lean_project_path}")
        except Exception as e:
            client = LeanLSPClient(lean_project_path, initial_build=False, print_warnings=False)
            logger.error(f"Could not do initial build, error: {e}")
    ctx.request_context.lifespan_context.client = client


def setup_client_for_file(ctx: Context, file_path: str) -> str | None:
    """Check if the current LSP client is already set up and correct for this file. Otherwise, set it up."""
    # Check if the file_path works for the current lean_project_path.
    lean_project_path = ctx.request_context.lifespan_context.lean_project_path
    if lean_project_path is not None:
        rel_path = get_relative_file_path(lean_project_path, file_path)
        if rel_path is not None:
            startup_client(ctx)
            return rel_path

    # Try to find the new correct project path by checking all directories in file_path.
    file_path_obj = Path(file_path)
    rel_path = None
    for parent_dir in file_path_obj.parents:
        if valid_lean_project_path(str(parent_dir)):
            lean_project_path = str(parent_dir)
            rel_path = get_relative_file_path(lean_project_path, file_path)
            if rel_path is not None:
                ctx.request_context.lifespan_context.lean_project_path = lean_project_path
                startup_client(ctx)
                break

    return rel_path


def update_file(ctx: Context, rel_path: str) -> str:
    """Update the file contents in the context."""
    # Get file contents and hash
    abs_path = str(Path(ctx.request_context.lifespan_context.lean_project_path) / rel_path)
    file_content = get_file_contents(abs_path)
    hashed_file = hash(file_content)

    # Check if file_contents have changed
    file_content_hashes: dict[str, str] = ctx.request_context.lifespan_context.file_content_hashes
    if rel_path not in file_content_hashes:
        file_content_hashes[rel_path] = hashed_file
        return file_content

    elif hashed_file == file_content_hashes[rel_path]:
        return file_content

    # Update file_contents
    file_content_hashes[rel_path] = hashed_file

    # Reload file in LSP
    client: LeanLSPClient = ctx.request_context.lifespan_context.client
    with contextlib.suppress(Exception):
        client.close_files([rel_path])
    return file_content


# LEAN CLIENT TOOL IMPLEMENTATIONS
def lean_build_impl(ctx: Context, lean_project_path: str | None = None, clean: bool = False) -> str:
    """Build the Lean project and restart the LSP Server."""
    if not lean_project_path:
        lean_project_path = ctx.request_context.lifespan_context.lean_project_path
    else:
        lean_project_path = str(Path(lean_project_path).resolve())
        ctx.request_context.lifespan_context.lean_project_path = lean_project_path

    build_output = ""
    try:
        client: LeanLSPClient = ctx.request_context.lifespan_context.client
        if client:
            client.close()
            ctx.request_context.lifespan_context.file_content_hashes.clear()

        if clean:
            subprocess.run(["lake", "clean"], cwd=lean_project_path, check=False)
            logger.info("Ran `lake clean`")

        with OutputCapture() as output:
            client = LeanLSPClient(
                lean_project_path,
                initial_build=True,
                print_warnings=False,
            )
        logger.info("Built project and re-started LSP client")

        ctx.request_context.lifespan_context.client = client
        build_output = output.get_output()
        return build_output
    except Exception as e:
        return f"Error during build:\n{e!s}\n{build_output}"


def lean_file_contents_impl(ctx: Context, file_path: str, annotate_lines: bool = True) -> str:
    """Get the text contents of a Lean file, optionally with line numbers."""
    try:
        data = get_file_contents(file_path)
    except FileNotFoundError:
        return f"File `{file_path}` does not exist. Please check the path and try again."

    if annotate_lines:
        data = data.split("\n")
        max_digits = len(str(len(data)))
        annotated = ""
        for i, line in enumerate(data):
            annotated += f"{i + 1}{' ' * (max_digits - len(str(i + 1)))}: {line}\n"
        return annotated
    else:
        return data


def lean_diagnostic_messages_impl(ctx: Context, file_path: str) -> list[str] | str:
    """Get all diagnostic msgs (errors, warnings, infos) for a Lean file."""
    rel_path = setup_client_for_file(ctx, file_path)
    if not rel_path:
        return "Invalid Lean file path: Unable to start LSP server or load file"

    update_file(ctx, rel_path)

    client: LeanLSPClient = ctx.request_context.lifespan_context.client
    diagnostics = client.get_diagnostics(rel_path)
    return format_diagnostics(diagnostics)


def lean_goal_impl(ctx: Context, file_path: str, line: int, column: int | None = None) -> str:
    """Get the proof goals (proof state) at a specific location in a Lean file."""
    rel_path = setup_client_for_file(ctx, file_path)
    if not rel_path:
        return "Invalid Lean file path: Unable to start LSP server or load file"

    content = update_file(ctx, rel_path)
    client: LeanLSPClient = ctx.request_context.lifespan_context.client

    if column is None:
        lines = content.splitlines()
        if line < 1 or line > len(lines):
            return "Line number out of range. Try elsewhere?"
        column_end = len(lines[line - 1])
        column_start = next((i for i, c in enumerate(lines[line - 1]) if not c.isspace()), 0)
        goal_start = client.get_goal(rel_path, line - 1, column_start)
        goal_end = client.get_goal(rel_path, line - 1, column_end)

        if goal_start is None and goal_end is None:
            return f"No goals on line:\n{lines[line - 1]}\nTry another line?"

        start_text = format_goal(goal_start, "No goals at line start.")
        end_text = format_goal(goal_end, "No goals at line end.")
        return f"Goals on line:\n{lines[line - 1]}\nBefore:\n{start_text}\nAfter:\n{end_text}"

    else:
        goal = client.get_goal(rel_path, line - 1, column - 1)
        f_goal = format_goal(goal, "Not a valid goal position. Try elsewhere?")
        f_line = format_line(content, line, column)
        return f"Goals at:\n{f_line}\n{f_goal}"


def lean_term_goal_impl(ctx: Context, file_path: str, line: int, column: int | None = None) -> str:
    """Get the expected type (term goal) at a specific location in a Lean file."""
    rel_path = setup_client_for_file(ctx, file_path)
    if not rel_path:
        return "Invalid Lean file path: Unable to start LSP server or load file"

    content = update_file(ctx, rel_path)
    if column is None:
        lines = content.splitlines()
        if line < 1 or line > len(lines):
            return "Line number out of range. Try elsewhere?"
        column = len(content.splitlines()[line - 1])

    client: LeanLSPClient = ctx.request_context.lifespan_context.client
    term_goal = client.get_term_goal(rel_path, line - 1, column - 1)
    f_line = format_line(content, line, column)
    if term_goal is None:
        return f"Not a valid term goal position:\n{f_line}\nTry elsewhere?"
    rendered = term_goal.get("goal", None)
    if rendered is not None:
        rendered = rendered.replace("```lean\n", "").replace("\n```", "")
    return f"Term goal at:\n{f_line}\n{rendered or 'No term goal found.'}"


def lean_hover_info_impl(ctx: Context, file_path: str, line: int, column: int) -> str:
    """Get hover info (docs for syntax, variables, functions, etc.) at a specific location in a Lean file."""
    rel_path = setup_client_for_file(ctx, file_path)
    if not rel_path:
        return "Invalid Lean file path: Unable to start LSP server or load file"

    file_content = update_file(ctx, rel_path)
    client: LeanLSPClient = ctx.request_context.lifespan_context.client
    hover_info = client.get_hover(rel_path, line - 1, column - 1)
    if hover_info is None:
        f_line = format_line(file_content, line, column)
        return f"No hover information at position:\n{f_line}\nTry elsewhere?"

    # Get the symbol and the hover information
    h_range = hover_info.get("range")
    symbol = extract_range(file_content, h_range)
    info = hover_info["contents"].get("value", "No hover information available.")
    info = info.replace("```lean\n", "").replace("\n```", "").strip()

    # Add diagnostics if available
    diagnostics = client.get_diagnostics(rel_path)
    filtered = filter_diagnostics_by_position(diagnostics, line - 1, column - 1)

    msg = f"Hover info `{symbol}`:\n{info}"
    if filtered:
        msg += "\n\nDiagnostics\n" + "\n".join(format_diagnostics(filtered))
    return msg


def lean_completions_impl(ctx: Context, file_path: str, line: int, column: int, max_completions: int = 32) -> str:
    """Get code completions at a location in a Lean file."""
    rel_path = setup_client_for_file(ctx, file_path)
    if not rel_path:
        return "Invalid Lean file path: Unable to start LSP server or load file"
    content = update_file(ctx, rel_path)

    client: LeanLSPClient = ctx.request_context.lifespan_context.client
    completions = client.get_completions(rel_path, line - 1, column - 1)
    formatted = [c["label"] for c in completions if "label" in c]
    f_line = format_line(content, line, column)

    if not formatted:
        return f"No completions at position:\n{f_line}\nTry elsewhere?"

    # Find the sort term: The last word/identifier before the cursor
    lines = content.splitlines()
    prefix = ""
    if 0 < line <= len(lines):
        text_before_cursor = lines[line - 1][: column - 1] if column > 0 else ""
        if not text_before_cursor.endswith("."):
            prefix = re.split(r"[\s()\[\]{},:;.]+", text_before_cursor)[-1].lower()

    # Sort completions: prefix matches first, then contains, then alphabetical
    if prefix:

        def sort_key(item):
            item_lower = item.lower()
            if item_lower.startswith(prefix):
                return (0, item_lower)
            elif prefix in item_lower:
                return (1, item_lower)
            else:
                return (2, item_lower)

        formatted.sort(key=sort_key)
    else:
        formatted.sort(key=str.lower)

    # Truncate if too many results
    if len(formatted) > max_completions:
        remaining = len(formatted) - max_completions
        formatted = [*formatted[:max_completions], f"{remaining} more, keep typing to filter further"]
    completions_text = "\n".join(formatted)
    return f"Completions at:\n{f_line}\n{completions_text}"


def lean_declaration_file_impl(ctx: Context, file_path: str, symbol: str) -> str:
    """Get the file contents where a symbol/lemma/class/structure is declared."""
    rel_path = setup_client_for_file(ctx, file_path)
    if not rel_path:
        return "Invalid Lean file path: Unable to start LSP server or load file"
    orig_file_content = update_file(ctx, rel_path)

    # Find the first occurence of the symbol (line and column) in the file,
    position = find_start_position(orig_file_content, symbol)
    if not position:
        return f"Symbol `{symbol}` (case sensitive) not found in file `{rel_path}`. Add it first, then try again."

    client: LeanLSPClient = ctx.request_context.lifespan_context.client
    declaration = client.get_declarations(rel_path, position["line"], position["column"])

    if len(declaration) == 0:
        return f"No declaration available for `{symbol}`."

    # Load the declaration file
    declaration = declaration[0]
    uri = declaration.get("targetUri")
    if not uri:
        uri = declaration.get("uri")

    abs_path = client._uri_to_abs(uri)
    if not Path(abs_path).exists():
        return f"Could not open declaration file `{abs_path}` for `{symbol}`."

    file_content = get_file_contents(abs_path)

    return f"Declaration of `{symbol}`:\n{file_content}"


def lean_multi_attempt_impl(ctx: Context, file_path: str, line: int, snippets: list[str]) -> list[str] | str:
    """Try multiple Lean code snippets at a line and get the goal state and diagnostics for each."""
    rel_path = setup_client_for_file(ctx, file_path)
    if not rel_path:
        return "Invalid Lean file path: Unable to start LSP server or load file"
    update_file(ctx, rel_path)
    client: LeanLSPClient = ctx.request_context.lifespan_context.client

    client.open_file(rel_path)

    results = []
    snippets[0] += "\n"  # Extra newline for the first snippet
    for snippet in snippets:
        # Create a DocumentContentChange for the snippet
        change = DocumentContentChange(
            snippet + "\n",
            [line - 1, 0],
            [line, 0],
        )
        # Apply the change to the file, capture diagnostics and goal state
        diag = client.update_file(rel_path, [change])
        formatted_diag = "\n".join(format_diagnostics(diag, select_line=line - 1))
        goal = client.get_goal(rel_path, line - 1, len(snippet))
        formatted_goal = format_goal(goal, "Missing goal")
        results.append(f"{snippet}:\n {formatted_goal}\n\n{formatted_diag}")

    # Make sure it's clean after the attempts
    client.close_files([rel_path])
    return results


def lean_run_code_impl(ctx: Context, code: str) -> list[str] | str:
    """Run a complete, self-contained code snippet and return diagnostics."""
    lean_project_path = ctx.request_context.lifespan_context.lean_project_path
    if lean_project_path is None:
        return (
            "No valid Lean project path found. Run another tool (e.g. `lean_diagnostic_messages`) "
            "first to set it up or set the LEAN_PROJECT_PATH environment variable."
        )

    rel_path = "temp_snippet.lean"
    abs_path = Path(lean_project_path) / rel_path

    try:
        abs_path.write_text(code)
    except Exception as e:
        return f"Error writing code snippet to file `{abs_path}`:\n{e!s}"

    client: LeanLSPClient = ctx.request_context.lifespan_context.client
    diagnostics = format_diagnostics(client.get_diagnostics(rel_path))
    client.close_files([rel_path])

    try:
        abs_path.unlink()
    except Exception as e:
        return f"Error removing temporary file `{abs_path}`:\n{e!s}"

    return diagnostics if diagnostics else "No diagnostics found for the code snippet (compiled successfully)."
