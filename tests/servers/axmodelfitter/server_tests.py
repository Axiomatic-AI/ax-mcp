"""Test files for auxiliary functions used in axmodelfitter's server."""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from fastmcp.client import Client

from axiomatic_mcp.servers.axmodelfitter.server import mcp
from axiomatic_mcp.servers.axmodelfitter.services.covariance_service import CovarianceService

@pytest_asyncio.fixture
async def main_mcp_client():
    async with Client(transport=mcp) as mcp_client:
        yield mcp_client

@pytest.mark.asyncio
async def test_list_tools(main_mcp_client):
    list_tools = await main_mcp_client.list_tools()
    assert len(list_tools) == 7
    assert "compute_parameter_covariance" in [tool.name for tool in list_tools]

@pytest.mark.asyncio
async def test_compute_parameter_covariance(main_mcp_client, tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("x,y\n1.0,2.0\n2.0,4.0\n3.0,6.0\n")

    mock_result = {
        "success": True,
        "markdown_report": "# Report",
        "parameters": [{"name": "a", "value": {"magnitude": 2.0, "unit": "dimensionless"}}],
        "sandwich_covariance": [[0.01]],
        "inverse_hessian_covariance": [[0.01]],
        "sandwich_correlation": [[1.0]],
        "inverse_hessian_correlation": [[1.0]],
        "parameter_names": ["a"],
        "sandwich_std_errors": [0.1],
        "inverse_hessian_std_errors": [0.1],
    }

    with patch.object(CovarianceService, "compute_covariance", new=AsyncMock(return_value=mock_result)):
        response = await main_mcp_client.call_tool("compute_parameter_covariance", {
            "model_name": "Linear",
            "function_source": "def f(a: float, x: float) -> float:\n    return a * x",
            "function_name": "f",
            "parameters": [{"name": "a", "value": {"magnitude": 2.0, "unit": "dimensionless"}}],
            "bounds": [
                {"name": "a", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
                {"name": "x", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
                {"name": "y", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 20.0, "unit": "dimensionless"}},
            ],
            "data_file": str(csv),
            "input_data": [{"column": "x", "name": "x", "unit": "dimensionless"}],
            "output_data": {"columns": "y", "name": "y", "unit": "dimensionless"},
        })

    assert response.content[0].text == "# Report"
    assert response.structured_content["sandwich_covariance"] == [[0.01]]
    assert response.structured_content["inverse_hessian_covariance"] == [[0.01]]


