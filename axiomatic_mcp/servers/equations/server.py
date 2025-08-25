from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult

from axiomatic_mcp.shared.documents.pdf_to_markdown import pdf_to_markdown

from ...shared import AxiomaticAPIClient

mcp = FastMCP(
    name="Axiomatic Equations Server",
    instructions="""This server provides tools to compose and analyze equations.""",
    version="0.0.1",
)


@mcp.tool(
    name="compose_expression",
    description="Compose an expression for a given task",
    tags=["equations", "compose"],
)
async def compose_expression(file_path: Annotated[Path, "The absolute path to the PDF file to analyze"], task: str) -> ToolResult:
    try:
        response = await pdf_to_markdown(file_path)

        input_body = {
            "source_document": response.markdown,
            "task": task,
        }

        response = AxiomaticAPIClient().post("/document/expression/compose", input_body=input_body)

        return ToolResult(
            composed_expression=response["composed_expression"], comments=response["comments"], composition_code=response["composition_code"]
        )

    except Exception as e:
        raise ToolError(f"Failed to analyze PDF document: {e!s}") from e
