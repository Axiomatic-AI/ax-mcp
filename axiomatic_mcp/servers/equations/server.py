from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from axiomatic_mcp.shared.documents.pdf_to_markdown import pdf_to_markdown

from ...shared import AxiomaticAPIClient

mcp = FastMCP(
    name="Axiomatic Equations Server",
    instructions="""This server provides tools to compose and analyze equations.""",
    version="0.0.1",
)


@mcp.tool(
    name="compose_expression",
    description=(
        "Compose an expression of your interest given the information form the source documents "
        "and equations residing there. Provide descrption of the expression you want to compose."
    ),
    tags=["equations", "compose"],
)
async def compose_expression(
    file_path: Annotated[Path, "The absolute path to the PDF file to analyze"], task: Annotated[str, "The task to be done for expression composition"]
) -> ToolResult:
    """If you have scientific text with equations, but you dont see the equation you're
    interested in then use this tool and simply say: >>Express the energy in terms of
     valocity and position<<, or something like that. The tool will return the desired expression
     together with sympy code that explain how it was derived."""
    try:
        response = await pdf_to_markdown(file_path)

        input_body = {"source_doc": response.markdown, "task": task}

        response = AxiomaticAPIClient().post("/document/expression/compose", data=input_body)

        return ToolResult(
            content=[
                TextContent(type="text", text=f"Composed expression: {response.get('composed_expression')}"),
                TextContent(type="text", text=f"Comments: {response.get('comments')}"),
                TextContent(type="text", text=f"Composition code: {response.get('composition_code')}"),
            ]
        )

    except Exception as e:
        raise ToolError(f"Failed to analyze PDF document: {e!s}") from e
