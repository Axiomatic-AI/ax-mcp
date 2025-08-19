"""Plot Parser MCP server"""

import random
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from pydantic import BaseModel

from ...shared import AxiomaticAPIClient


class ExtractedSeries(BaseModel):
    """Extracted series from a plot"""

    id: int
    points: list[tuple[float, float]]


class PlotData(BaseModel):
    """New plot parser output for v2, will replace old PlotParserOutput"""

    extracted_series: list[ExtractedSeries]


def process_plot_parser_output(response_json, max_points: int = 100, sig_figs: int = 5) -> PlotData:
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

        series = ExtractedSeries(id=extracted_series["id"], points=condensed_points_list)
        extracted_series_list.append(series)

    return PlotData(extracted_series=extracted_series_list)


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
    plot_path: Annotated[Path, "The absolute path to the image file of the plot to analyze"],
) -> Annotated[PlotData, "Extracted plot data containing series and points from the plot image"]:
    if not plot_path.exists():
        raise FileNotFoundError(f"Image not found: {plot_path}")

    with Path.open(plot_path, "rb") as f:
        files = {"plot_img": ("plot.png", f, "image/png")}
        params = {"get_img_coords": True, "v2": True}
        response = AxiomaticAPIClient().post("/document/plot/points", files=files, params=params)

    return process_plot_parser_output(response)
