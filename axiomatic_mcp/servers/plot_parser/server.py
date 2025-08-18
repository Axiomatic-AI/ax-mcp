"""Documents MCP server for filesystem document operations."""

from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP

from ...shared import AxiomaticAPIClient

plot_parser_server = FastMCP(
    name="Plot Parser Server",
    instructions="""This server hosts tools to parse and understand images of plots""",
    version="0.0.1",
)


@plot_parser_server.tool(
    name="extract_data_from_plot_image",
    description="Extracts data from an image of a plot",
    tags=["plot", "filesystem", "analyze"],
)
async def extract_data_from_plot_image(
    plot_path: Annotated[Path, "The absolute path to the image file of the plot to analyze"],
) -> Annotated[str, "A string of markdown text of the analyzed document"]:
    if not plot_path.exists():
        raise FileNotFoundError(f"Document not found: {plot_path}")

    data = {"get_img_coords": "true", "v2": "true"}

    with Path.open(plot_path, "rb") as f:
        files = {"plot_img": ("plot.png", f, "image/png")}
        response = AxiomaticAPIClient().post("/document/plot/points", files=files, data=data)

    return str(response)
