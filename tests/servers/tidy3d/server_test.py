"""Tests for the AxTidy3D MCP server."""

from unittest.mock import patch

import pytest
import pytest_asyncio
from fastmcp.client import Client

from axiomatic_mcp.servers.tidy3d.server import mcp
from axiomatic_mcp.servers.tidy3d.services.tidy3d_service import Tidy3DService


@pytest_asyncio.fixture
async def mcp_client():
    async with Client(transport=mcp) as client:
        yield client


@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    tools = await mcp_client.list_tools()
    tool_names = {t.name for t in tools}
    assert {"generate_code", "execute_code", "start_simulation", "get_simulation_status"} <= tool_names


@pytest.mark.asyncio
async def test_generate_code_backend_error(mcp_client):
    mock_response = {"code": None, "explanation": None, "error": "LLM timeout"}

    with patch.object(Tidy3DService, "generate_code", return_value=mock_response):
        response = await mcp_client.call_tool("generate_code", {"problem_description": "Simulate a waveguide."})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("LLM timeout" in t for t in texts)


@pytest.mark.asyncio
async def test_execute_code_local_success(mcp_client):
    mock_response = {
        "success": True,
        "result": {"n_eff": [2.1]},
        "error": None,
        "stdout": "",
        "execution_time": 0.42,
        "task_id": None,
        "task_status": None,
        "estimated_cost_flex_credits": None,
    }

    with patch.object(Tidy3DService, "execute_code", return_value=mock_response):
        response = await mcp_client.call_tool("execute_code", {"code": "export('n_eff', [2.1])"})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("n_eff" in t for t in texts)
    assert not any("task_id" in t for t in texts)


@pytest.mark.asyncio
async def test_execute_code_cloud_estimate_never_auto_starts(mcp_client):
    mock_response = {
        "success": True,
        "result": None,
        "error": None,
        "stdout": "",
        "execution_time": 1.2,
        "task_id": "fdve-abc123",
        "task_status": "estimated",
        "estimated_cost_flex_credits": 0.5,
    }

    with patch.object(Tidy3DService, "execute_code", return_value=mock_response) as mock_execute, patch.object(
        Tidy3DService, "start_task"
    ) as mock_start:
        response = await mcp_client.call_tool("execute_code", {"code": "submit_to_cloud(sim)"})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("fdve-abc123" in t and "0.5 Flex credits" in t and "NOT started" in t for t in texts)
    mock_execute.assert_called_once()
    mock_start.assert_not_called()


@pytest.mark.asyncio
async def test_start_simulation(mcp_client):
    mock_response = {"task_id": "fdve-abc123", "task_status": "running"}

    with patch.object(Tidy3DService, "start_task", return_value=mock_response) as mock_start:
        response = await mcp_client.call_tool("start_simulation", {"task_id": "fdve-abc123"})

    mock_start.assert_called_once_with("fdve-abc123", None)
    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("running" in t for t in texts)


@pytest.mark.asyncio
async def test_get_simulation_status_reports_cost(mcp_client):
    mock_response = {"task_id": "fdve-abc123", "task_status": "success", "real_cost_flex_credits": 0.47}

    with patch.object(Tidy3DService, "get_task_status", return_value=mock_response):
        response = await mcp_client.call_tool("get_simulation_status", {"task_id": "fdve-abc123"})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("success" in t and "0.47 Flex credits" in t for t in texts)
