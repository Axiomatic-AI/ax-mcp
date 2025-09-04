"""Model Builder MCP server."""

import asyncio
import json
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...shared.api_client import AxiomaticAPIClient
from ...shared.utils.get_unique_filename import get_unique_filename
from .models.physics_model_proposer_response import PhysicsModelProposerResponse

mcp = FastMCP(
    name="Axiomatic Model Builder",
    instructions="""This server provides tools to build models.""",
    version="0.0.1",
)


@mcp.tool(
    name="build_model",
    description="Build a model using the Axiomatic_AI Platform. The model will be built using and fitting the data in the csv file and \
    insights from the pdf file.",
    tags=["model", "build"],
)
async def build_model(
    file_path: Annotated[Path, "The absolute path to the PDF file to analyze"],
    data_path: Annotated[Path, "The absolute path to the csv data file to analyze"],
    query: Annotated[str, "The query to use for the model building"],
) -> ToolResult:
    """Build a model using the Axiomatic_AI Platform. The model will be built using and fitting the data in the csv file and \
        insights from the pdf file."""
    return await _build_model_impl(file_path, data_path, query)


def format_response(filename: str, query: str) -> str:
    """Format the physics model proposer response."""

    return f"""**Physics Model Generated from {filename}**

**Query:** {query}
"""


async def _build_model_impl(
    file_path: Path,
    data_path: Path,
    query: str,
) -> ToolResult:
    """Internal implementation of build_model without MCP decoration."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.suffix.lower() != ".pdf":
        raise ValueError("File must be a PDF")

    if not data_path.exists():
        raise FileNotFoundError(f"File not found: {data_path}")
    if data_path.suffix.lower() != ".csv":
        raise ValueError("File must be a CSV")

    try:
        file_content = await asyncio.to_thread(file_path.read_bytes)
        data_content = await asyncio.to_thread(data_path.read_bytes)

        files = {
            "file": (file_path.name, file_content, "application/pdf"),
            "data": (data_path.name, data_content, "text/csv"),
        }

        # Make API call
        response = await asyncio.to_thread(
            AxiomaticAPIClient().post,
            "/physics-models/",
            files=files,
            data={"query": query},
        )

        validated_response = PhysicsModelProposerResponse.model_validate(response)
        formatted_response = format_response(file_path.name, query)

        physics_model_path = get_unique_filename(file_path.parent, "physics_model.py")
        parameters_path = get_unique_filename(file_path.parent, "parameters.json")

        with Path.open(physics_model_path, "w", encoding="utf-8") as f:
            f.write(validated_response.physics_model_code)

        with Path.open(parameters_path, "w", encoding="utf-8") as f:
            json.dump(validated_response.parameters, f)

        return ToolResult(
            content=[TextContent(type="text", text=f"Successfully built model: \n {formatted_response}")],
            structured_content={
                "physics_model_code": validated_response.physics_model_code,
                "parameters": validated_response.parameters,
                "optimization_results": validated_response.optimization_results,
                "last_message": validated_response.last_message,
            },
        )

    except Exception as e:
        raise ToolError("Error building model") from e
