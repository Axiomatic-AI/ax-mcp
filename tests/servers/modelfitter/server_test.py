"""Tests for the AxModelFitterV2 MCP server."""

import pytest
import pytest_asyncio
from unittest.mock import patch
from fastmcp.client import Client

from axiomatic_mcp.servers.modelfitter.server import mcp
from axiomatic_mcp.servers.modelfitter.services.model_fitter_service import ModelFitterService


@pytest_asyncio.fixture
async def mcp_client():
    async with Client(transport=mcp) as client:
        yield client


@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    tools = await mcp_client.list_tools()
    tool_names = {t.name for t in tools}
    assert {"generate_code", "execute_code"} <= tool_names


@pytest.mark.asyncio
async def test_generate_code_backend_error(mcp_client):
    mock_response = {"code": None, "explanation": None, "error": "LLM timeout"}

    with patch.object(ModelFitterService, "generate_code", return_value=mock_response):
        response = await mcp_client.call_tool("generate_code", {"problem_description": "Fit something."})

    assert any("LLM timeout" in c.text for c in response.content if hasattr(c, "text"))


@pytest.mark.asyncio
async def test_execute_code_failure(mcp_client):
    mock_response = {
        "success": False,
        "result": None,
        "stdout": "Traceback (most recent call last):\n  ...",
        "execution_time": 0.1,
        "error": "NameError: name 'fit' is not defined",
    }

    with patch.object(ModelFitterService, "execute_code", return_value=mock_response):
        response = await mcp_client.call_tool("execute_code", {"code": "fit()"})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("NameError" in t for t in texts)
    assert any("Traceback" in t for t in texts)
