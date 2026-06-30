"""Tests for the AxModelFitterV2 MCP server."""

from unittest.mock import patch

import pytest
import pytest_asyncio
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


# execute_code forwards a data_file through to the service.
@pytest.mark.asyncio
async def test_execute_code_accepts_data_file(mcp_client, tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("t,y\n0.0,1.0\n1.0,2.5\n")
    captured = {}

    def _fake_execute(self, code, data_file=None, columns=None):
        captured["data_file"] = data_file
        return {"success": True, "result": {"ok": 1}, "stdout": None, "execution_time": 0.0}

    with patch.object(ModelFitterService, "execute_code", _fake_execute):
        response = await mcp_client.call_tool(
            "execute_code",
            {"code": "export('ok', 1)", "data_file": str(p)},
        )

    assert captured["data_file"] == str(p)
    assert any("ok" in c.text for c in response.content if hasattr(c, "text"))


# A data-inlining failure surfaces as a ToolError, before any API call.
@pytest.mark.asyncio
async def test_execute_code_data_file_error_is_toolerror(mcp_client):
    from fastmcp.exceptions import ToolError

    with pytest.raises(ToolError, match="Data file error"):
        await mcp_client.call_tool(
            "execute_code",
            {"code": "export('ok', 1)", "data_file": "/no/such/file.csv"},
        )


# preview_data returns the file's columns so the agent can choose what to inline.
@pytest.mark.asyncio
async def test_preview_data_returns_columns(mcp_client, tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("t,temp,note\n0.0,1.0,a\n1.0,2.0,b\n")
    response = await mcp_client.call_tool("preview_data", {"data_file": str(p)})
    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("temp" in t for t in texts)


# preview_data maps a bad path to a ToolError.
@pytest.mark.asyncio
async def test_preview_data_error_is_toolerror(mcp_client):
    from fastmcp.exceptions import ToolError

    with pytest.raises(ToolError, match="Data file error"):
        await mcp_client.call_tool("preview_data", {"data_file": "/no/such/file.csv"})


# The server exposes exactly the three expected tools.
@pytest.mark.asyncio
async def test_list_tools_includes_preview(mcp_client):
    tools = await mcp_client.list_tools()
    names = {t.name for t in tools}
    assert {"generate_code", "execute_code", "preview_data"} <= names
