"""Documents MCP server for filesystem document operations."""

import base64
import re
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.documents.pdf_to_markdown import pdf_to_markdown
from ...shared.utils.prompt_utils import get_feedback_prompt

mcp = FastMCP(
    name="AxDocumentParser Server",
    instructions="""This server provides tools to read, analyze, and process documents
    from the filesystem using the Axiomatic_AI Platform.
    """
    + get_feedback_prompt("parse_pdf_to_md"),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)


@mcp.tool(
    name="parse_pdf_to_md",
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

        counter = 1
        for image_name, base64_string in response.images.items():
            renamed_image = f"{file_path.stem}_fig_{counter}.png"

            image_path = file_path.parent / renamed_image

            if base64_string.startswith("data:image/"):
                image_data = re.match(r"data:image/[^;]+;base64,(.*)", base64_string).group(1)
            else:
                image_data = base64_string

            with Path.open(image_path, "wb") as image_file:
                image_file.write(base64.b64decode(image_data))

            markdown = markdown.replace(image_name, renamed_image)
            counter += 1

        with Path.open(name, "w", encoding="utf-8") as f:
            f.write(markdown)

        return ToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Generated markdown at: {name}\nImages saved in: {file_path.parent}",
                )
            ],
            structured_content={
                "markdown_path": name,
                "markdown_preview": markdown[:1000],
                "images_path": file_path.parent,
                "images_count": len(response.images),
            },
        )
    except Exception as e:
        raise ToolError(f"Failed to analyze PDF document: {e!s}") from e
