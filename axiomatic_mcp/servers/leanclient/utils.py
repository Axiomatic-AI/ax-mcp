import os
import sys
import tempfile
from pathlib import Path

from mcp.server.auth.provider import AccessToken, TokenVerifier


class StdoutToStderr:
    """Redirects stdout to stderr at the file descriptor level bc lake build logging"""

    def __init__(self):
        self.original_stdout_fd = None

    def __enter__(self):
        self.original_stdout_fd = os.dup(sys.stdout.fileno())
        stderr_fd = sys.stderr.fileno()
        os.dup2(stderr_fd, sys.stdout.fileno())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_stdout_fd is not None:
            os.dup2(self.original_stdout_fd, sys.stdout.fileno())
            os.close(self.original_stdout_fd)
            self.original_stdout_fd = None


class OutputCapture:
    """Capture any output to stdout and stderr at the file descriptor level."""

    def __init__(self):
        self.original_stdout_fd = None
        self.original_stderr_fd = None
        self.temp_file = None
        self.captured_output = ""

    def __enter__(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        self.original_stdout_fd = os.dup(sys.stdout.fileno())
        self.original_stderr_fd = os.dup(sys.stderr.fileno())
        os.dup2(self.temp_file.fileno(), sys.stdout.fileno())
        os.dup2(self.temp_file.fileno(), sys.stderr.fileno())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.dup2(self.original_stdout_fd, sys.stdout.fileno())
        os.dup2(self.original_stderr_fd, sys.stderr.fileno())
        os.close(self.original_stdout_fd)
        os.close(self.original_stderr_fd)

        self.temp_file.flush()
        self.temp_file.seek(0)
        self.captured_output = self.temp_file.read()
        self.temp_file.close()
        Path(self.temp_file.name).unlink()

    def get_output(self):
        return self.captured_output


class OptionalTokenVerifier(TokenVerifier):
    def __init__(self, expected_token: str):
        self.expected_token = expected_token

    async def verify_token(self, token: str) -> AccessToken | None:
        if token == self.expected_token:
            return AccessToken(token=token, client_id="lean-lsp-mcp", scopes=["user"])
        return None


def get_file_contents(abs_path: str) -> str:
    """Read file contents with multiple encoding fallbacks."""
    path = Path(abs_path)
    for enc in ("utf-8", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding=None)


def format_diagnostics(diagnostics: list[dict], select_line: int = -1) -> list[str]:
    """Format the diagnostics messages."""
    msgs = []
    if select_line != -1:
        diagnostics = filter_diagnostics_by_position(diagnostics, select_line, None)

    # Format more compact
    for diag in diagnostics:
        r = diag.get("fullRange", diag.get("range", None))
        if r is None:
            r_text = "No range"
        else:
            r_text = f"l{r['start']['line'] + 1}c{r['start']['character'] + 1}-l{r['end']['line'] + 1}c{r['end']['character'] + 1}"
        msgs.append(f"{r_text}, severity: {diag['severity']}\n{diag['message']}")
    return msgs


def format_goal(goal, default_msg):
    """Format goal output."""
    if goal is None:
        return default_msg
    rendered = goal.get("rendered")
    return rendered.replace("```lean\n", "").replace("\n```", "") if rendered else default_msg


def extract_range(content: str, range: dict) -> str:
    """Extract the text from the content based on the range."""
    start_line = range["start"]["line"]
    start_char = range["start"]["character"]
    end_line = range["end"]["line"]
    end_char = range["end"]["character"]

    lines = content.splitlines()
    if start_line < 0 or end_line >= len(lines):
        return "Range out of bounds"
    if start_line == end_line:
        return lines[start_line][start_char:end_char]
    else:
        selected_lines = lines[start_line : end_line + 1]
        selected_lines[0] = selected_lines[0][start_char:]
        selected_lines[-1] = selected_lines[-1][:end_char]
        return "\n".join(selected_lines)


def find_start_position(content: str, query: str) -> dict | None:
    """Find the position of the query in the content."""
    lines = content.splitlines()
    for line_number, line in enumerate(lines):
        char_index = line.find(query)
        if char_index != -1:
            return {"line": line_number, "column": char_index}
    return None


def format_line(
    file_content: str,
    line_number: int,
    column: int | None = None,
    cursor_tag: str | None = "<cursor>",
) -> str:
    """Show a line and cursor position in a file."""
    lines = file_content.splitlines()
    line_number -= 1
    if line_number < 0 or line_number >= len(lines):
        return "Line number out of range"
    line = lines[line_number]
    if column is None:
        return line
    column -= 1
    if column < 0 or column >= len(line):
        return "Invalid column number"
    return f"{line[:column]}{cursor_tag}{line[column:]}"


def filter_diagnostics_by_position(diagnostics: list[dict], line: int, column: int | None) -> list[dict]:
    """Find diagnostics at a specific position."""
    if column is None:
        return [d for d in diagnostics if d["range"]["start"]["line"] <= line <= d["range"]["end"]["line"]]

    return [
        d
        for d in diagnostics
        if d["range"]["start"]["line"] <= line <= d["range"]["end"]["line"]
        and d["range"]["start"]["character"] <= column < d["range"]["end"]["character"]
    ]


def valid_lean_project_path(path: str) -> bool:
    """Check if the given path is a valid Lean project path (contains a lean-toolchain file)."""
    path_obj = Path(path)
    if not path_obj.exists():
        return False
    return (path_obj / "lean-toolchain").is_file()


def get_relative_file_path(lean_project_path: str, file_path: str) -> str | None:
    """Convert path relative to project path."""
    lean_project = Path(lean_project_path)
    file_path_obj = Path(file_path)

    # Check if absolute path
    if file_path_obj.exists():
        return str(file_path_obj.relative_to(lean_project))

    # Check if relative to project path
    path = lean_project / file_path
    if path.exists():
        return str(path.relative_to(lean_project))

    # Check if relative to CWD
    cwd = Path.cwd()
    path = cwd / file_path
    if path.exists():
        return str(path.relative_to(lean_project))

    return None
