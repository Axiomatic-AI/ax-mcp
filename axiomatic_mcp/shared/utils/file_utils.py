import mimetypes


def get_file_type(file_path: str) -> str:
    """
    Get the MIME type of a file based on its extension.

    Args:
        file_path: Path to the file

    Returns:
        The MIME type of the file, or "application/octet-stream" if unknown
    """
    mimetypes.add_type("application/x-ipynb+json", ".ipynb", strict=True)
    mimetypes.add_type("text/markdown", ".md", strict=True)
    mimetypes.add_type("text/markdown", ".markdown", strict=True)
    mimetypes.add_type("text/markdown", ".MD", strict=True)
    mimetypes.add_type("text/markdown", ".mdx", strict=True)
    mime_type, _ = mimetypes.guess_type(file_path)

    return mime_type or "application/octet-stream"
