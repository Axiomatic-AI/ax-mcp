"""Utilities for handling code input processing."""

from pathlib import Path


async def get_python_code(code_input: Path | str) -> tuple[str, Path | None]:
    """Extract Python code from either a file path or direct string.

    Args:
        code_input: Either a Path object to a .py file or a string (file path or direct code)

    Returns:
        tuple[str, Path | None]:
            - code_content: The Python code to process
            - file_path: Path to the source file if input was a file, None if direct code
                        (Used to determine where to save output files)

    Raises:
        ValueError: If file not found or unsupported file type
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
        if potential_path.suffix.lower() == ".py":
            if not potential_path.exists():
                raise ValueError(f"File not found: {potential_path}")
            with Path.open(potential_path, encoding="utf-8") as f:
                return f.read(), potential_path
        if potential_path.exists():
            raise ValueError(f"Unsupported file type: {potential_path.suffix}. Only .py files are supported")

    # It's direct code content
    return code_input, None
