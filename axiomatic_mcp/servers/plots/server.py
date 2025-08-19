"""Plot Parser MCP server"""

import mimetypes
import random
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel

from ...shared import AxiomaticAPIClient


class SeriesPoints(BaseModel):
    """Extracted series from a plot"""

    id: int
    points: list[tuple[float, float]]


class SeriesPointsData(BaseModel):
    """A list of points from each series in a plot"""

    series_points: list[SeriesPoints]


def process_plot_parser_output(response_json, max_points: int = 100, sig_figs: int = 5) -> SeriesPointsData:
    extracted_series_list = []

    for extracted_series in response_json["extracted_series"]:
        all_extracted_points = extracted_series.get("points") or []
        if not all_extracted_points:
            continue

        selected_points = random.sample(all_extracted_points, min(max_points, len(all_extracted_points)))
        condensed_points_list = []
        for point in selected_points:
            x_val = float(format(point["value_x"], f".{sig_figs}g"))
            y_val = float(format(point["value_y"], f".{sig_figs}g"))
            condensed_points_list.append((x_val, y_val))

        series = SeriesPoints(id=extracted_series["id"], points=condensed_points_list)
        extracted_series_list.append(series)

    return SeriesPointsData(series_points=extracted_series_list)


PLOTS_SERVER_INSTRUCTIONS = """This server hosts tools for extracting numerical data from plot images. 
It can analyze line plots and scatter plots and convert visual data points into a structured numerical format."""

plots = FastMCP(
    name="Axiomatic plots tools server",
    instructions=PLOTS_SERVER_INSTRUCTIONS,
    version="0.0.1",
)


@plots.tool(
    name="extract_numerical_series_points_from_plot_image",
    description="Analyzes images of line and scatter plots to extract precise numerical data points from all series in the plot",
    tags={"plot", "filesystem", "analyze"},
)
async def extract_data_from_plot_image(
    plot_path: Annotated[
        Path, "The absolute path to the image file of the plot to analyze. Supports common image formats: PNG, JPEG/JPG, BMP, TIFF, WebP"
    ],
    max_number_points_per_series: Annotated[
        int,
        "Maximum points returned per series. Uses random sampling if plot contains more points than limit",
    ] = 100,
) -> Annotated[SeriesPointsData, "Extracted plot data containing series and points from the plot image"]:
    if not plot_path.is_file():
        raise FileNotFoundError(f"Image not found or is not a regular file: {plot_path}")

    supported_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
    file_extension = plot_path.suffix.lower()
    if file_extension not in supported_extensions:
        raise ToolError(f"Unsupported image format: {file_extension}. Supported formats: {', '.join(supported_extensions)}")

    mime_type, _ = mimetypes.guess_type(str(plot_path))
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "application/octet-stream"

    with Path.open(plot_path, "rb") as f:
        files = {"plot_img": (plot_path.name, f, mime_type)}
        params = {"get_img_coords": True, "v2": True}

        try:
            response = AxiomaticAPIClient().post("/document/plot/points", files=files, params=params)
        except Exception as e:
            raise ToolError(f"Failed to analyze plot image: {e!s}") from e

        if not isinstance(response, dict):
            raise ToolError("Upstream service returned non-JSON response")

        if "extracted_series" not in response:
            raise ToolError("Upstream service returned unexpected response format")

    return process_plot_parser_output(response, max_points=max_number_points_per_series)
