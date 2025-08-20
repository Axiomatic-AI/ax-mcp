"""Documents MCP server for filesystem document operations."""

from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...shared import AxiomaticAPIClient

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
    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValueError("File must be a PDF")

    file_content = file_path.read_bytes()
    files = {"file": (file_path.name, file_content, "application/pdf")}
    data = {"method": "mistral", "ocr": False, "layout_model": "doclayout_yolo"}

    response = AxiomaticAPIClient().post("/document/parse", files=files, data=data)
    markdown: str = response["markdown"]
    name = file_path.stem + ".md"
    return ToolResult(
        content=[TextContent(type="text", text=f"Generated markdown for: {name}\n\n```markdown\n{markdown}\n```")],
        structured_content={
            "suggestions": [{"type": "create_file", "path": name, "content": markdown, "description": f"Create {name} with the generated markdown"}]
        },
    )
