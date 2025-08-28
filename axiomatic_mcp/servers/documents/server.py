"""Documents MCP server for filesystem document operations."""

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
    description="Convert a PDF document to markdown using Axiomatic's advanced OCR.",
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

        return ToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Generated markdown for: {name}\n\n```markdown\n{markdown}\n```",
                )
            ],
        )
    except Exception as e:
        raise ToolError(f"Failed to analyze PDF document: {e!s}") from e
