"""AxPlotToData MCP server"""

import base64
import json
import math
import mimetypes
import random
import re
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent
from pydantic import BaseModel

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared import AxiomaticAPIClient
from ...shared.utils.prompt_utils import get_feedback_prompt


class Point(BaseModel):
    """Extracted point of a series from a plot"""

    x_value: float
    y_value: float


class SeriesPoints(BaseModel):
    """Extracted series from a plot"""

    series_unique_id: int
    points: list[Point]


class SeriesPointsData(BaseModel):
    """A list of points from each series in a plot"""

    series_points: list[SeriesPoints]


def process_plot_parser_output(response_json, max_points: int = 100, sig_figs: int = 5) -> SeriesPointsData:
    extracted_series_list: list[SeriesPoints] = []

    series_array = (response_json or {}).get("extracted_series") or []
    for idx, extracted_series in enumerate(series_array):
        all_extracted_points = extracted_series.get("points") or []
        if not all_extracted_points:
            continue

        sample_size = min(max_points, len(all_extracted_points))
        selected_points = random.sample(all_extracted_points, sample_size)

        condensed_points_list: list[Point] = []
        for point in selected_points:
            x_raw = point.get("value_x")
            y_raw = point.get("value_y")
            if x_raw is None or y_raw is None:
                continue
            try:
                x_num = float(x_raw)
                y_num = float(y_raw)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(x_num) or not math.isfinite(y_num):
                continue
            x_val = float(format(x_num, f".{sig_figs}g"))
            y_val = float(format(y_num, f".{sig_figs}g"))
            condensed_points_list.append(Point(x_value=x_val, y_value=y_val))
        if not condensed_points_list:
            continue

        series_id = extracted_series.get("id", idx)
        try:
            series_id = int(series_id)
        except (TypeError, ValueError):
            series_id = idx

        series = SeriesPoints(series_unique_id=series_id, points=condensed_points_list)
        extracted_series_list.append(series)
    return SeriesPointsData(series_points=extracted_series_list)


PLOTS_SERVER_INSTRUCTIONS = """This server hosts tools for extracting numerical data from plot images. 
It can analyze line plots and scatter plots and convert visual data points into a structured numerical format."""

plots = FastMCP(
    name="""AxPlotToData server
    """
    + get_feedback_prompt("extract_numerical_series"),
    instructions=PLOTS_SERVER_INSTRUCTIONS,
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)


@plots.tool(
    name="extract_numerical_series",
    description="Analyzes images of line and scatter plots to extract precise numerical data points from all series in the plot",
    tags={"plot", "filesystem", "analyze"},
)
async def extract_data_from_plot_image(
    plot_path: Annotated[Path, "The absolute path to the image file of the plot to analyze. Supports only PNG for now"],
    max_number_points_per_series: Annotated[
        int,
        "Maximum points returned per series. Uses random sampling if plot contains more points than limit",
    ] = 100,
) -> Annotated[ToolResult, "Extracted plot data containing series and points from the plot image"]:
    if not plot_path.is_file():
        raise FileNotFoundError(f"Image not found or is not a regular file: {plot_path}")

    supported_extensions = {".png"}
    file_extension = plot_path.suffix.lower()
    if file_extension not in supported_extensions:
        raise ValueError(f"Unsupported image format: {file_extension}. Supported formats: {', '.join(supported_extensions)}")

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

    series_data = process_plot_parser_output(response, max_points=max_number_points_per_series)

    json_path = plot_path.parent / (plot_path.stem + "_data.json")

    with Path.open(json_path, "w", encoding="utf-8") as f:
        json.dump(series_data.model_dump(), f, indent=2)

    return ToolResult(
        content=[
            TextContent(
                type="text",
                text=f"Extracted plot data saved to: {json_path}\n\n```json\n{json.dumps(series_data.model_dump(), indent=2)}\n```",
            )
        ],
    )


@plots.tool(
    name="split_multi_plot",
    description="Given an image of a plot with multiple subplots, splits it into the individual subplots",
    tags={"plot", "filesystem", "analyze"},
)
async def split_multi_plot(
    plot_path: Annotated[Path, "The absolute path to the image file of the plot to split. Supports only PNG for now"],
) -> Annotated[ToolResult, "Paths to the saved split images"]:
    if not plot_path.is_file():
        raise FileNotFoundError(f"Image not found or is not a regular file: {plot_path}")

    supported_extensions = {".png"}
    file_extension = plot_path.suffix.lower()
    if file_extension not in supported_extensions:
        raise ValueError(f"Unsupported image format: {file_extension}. Supported formats: {', '.join(supported_extensions)}")

    mime_type, _ = mimetypes.guess_type(str(plot_path))
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "application/octet-stream"

    with Path.open(plot_path, "rb") as f:
        files = {"plot_img": (plot_path.name, f, mime_type)}
        params = {"get_img_coords": True, "v2": True}

        try:
            response = AxiomaticAPIClient().post("/document/plot/split", files=files, params=params)
        except Exception as e:
            raise ToolError(f"Failed to split plot image: {e!s}") from e

        if not isinstance(response, (list, tuple)) or not all(isinstance(x, str) for x in response):
            raise ToolError("Upstream service returned unexpected response format; expected a list of base64-encoded image strings")
        if not response:
            raise ToolError("Upstream service returned no split images")

    split_image_paths = []

    for idx, b64_split_img in enumerate(response):
        split_image_path = plot_path.parent / (plot_path.stem + f"_split_{idx}.png")

        match = re.match(r"data:image/[^;]+;base64,(.*)", b64_split_img)
        image_data = match.group(1) if match else b64_split_img

        try:
            binary = base64.b64decode(image_data, validate=True)
        except Exception as e:
            raise ToolError(f"Invalid base64 image payload at index {idx}: {e!s}") from e

        split_image_path.write_bytes(binary)

        split_image_paths.append(split_image_path)

    return ToolResult(
        content=[
            TextContent(
                type="text",
                text=(f"Split into {len(split_image_paths)} images:\n" + "\n".join(f"- {p}" for p in split_image_paths)),
            ),
        ],
    )
