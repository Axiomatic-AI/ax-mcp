"""Documents MCP server for filesystem document operations."""

import base64
import re
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...shared.documents.pdf_to_markdown import pdf_to_markdown

mcp = FastMCP(
    name="Axiomatic Documents Server",
    instructions="""This server provides tools to read, analyze, and process documents
    from the filesystem using the Axiomatic_AI Platform.""",
    version="0.0.1",
)


@mcp.tool(
    name="document_to_markdown",
    description="""
    Convert a PDF document to markdown using Axiomatic's advanced OCR.
    The output will be a markdown file with the same name as the input file,
    and the images will be saved in the same directory as the input file.
    """,
    tags=["document", "filesystem", "analyze"],
)
async def document_to_markdown(
    file_path: Annotated[Path, "The absolute path to the PDF file to analyze"],
) -> ToolResult:
    try:
        response = await pdf_to_markdown(file_path)
        markdown = response.markdown
        name = file_path.parent / (file_path.stem + ".md")

        with Path.open(name, "w", encoding="utf-8") as f:
            f.write(markdown)

        for image_name, base64_string in response.images.items():
            image_path = file_path.parent / image_name

            if base64_string.startswith("data:image/"):
                image_data = re.match(r"data:image/[^;]+;base64,(.*)", base64_string).group(1)
            else:
                image_data = base64_string

            with Path.open(image_path, "wb") as image_file:
                image_file.write(base64.b64decode(image_data))

        return ToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Generated markdown for: {name}\nImages saved in: {file_path.parent}\n\n```markdown\n{markdown}\n```",
                )
            ],
        )
    except Exception as e:
        raise ToolError(f"Failed to analyze PDF document: {e!s}") from e
