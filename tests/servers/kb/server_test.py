"""Tests for the AxKnowledgeBase MCP server."""

from unittest.mock import patch

import pytest
import pytest_asyncio
from fastmcp.client import Client

from axiomatic_mcp.servers.kb.server import mcp
from axiomatic_mcp.servers.kb.services.knowledge_base_service import KnowledgeBaseService


@pytest_asyncio.fixture
async def mcp_client():
    async with Client(transport=mcp) as client:
        yield client


@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    tools = await mcp_client.list_tools()
    tool_names = {t.name for t in tools}
    assert {
        "search_knowledge_base",
        "get_knowledge_base_schema",
        "get_knowledge_base_overview",
        "list_knowledge_base_papers",
        "knowledge_graph_read",
    } <= tool_names


@pytest.mark.asyncio
async def test_search_knowledge_base_surfaces_citations(mcp_client):
    mock_response = {
        "query": "ring resonator loss",
        "results": [
            {
                "text": "Measured Q factors of 1e6 were reported for the silicon nitride ring.",
                "score": 0.87,
                "metadata": {"paper_id": "2301.07041", "paper_title": "Low-loss ring resonators"},
            }
        ],
        "count": 1,
    }

    with patch.object(KnowledgeBaseService, "search", return_value=mock_response):
        response = await mcp_client.call_tool("search_knowledge_base", {"query": "ring resonator loss"})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("Low-loss ring resonators" in t for t in texts)
    assert any("0.870" in t for t in texts)


@pytest.mark.asyncio
async def test_search_knowledge_base_no_results(mcp_client):
    mock_response = {"query": "nonexistent topic", "results": [], "count": 0}

    with patch.object(KnowledgeBaseService, "search", return_value=mock_response):
        response = await mcp_client.call_tool("search_knowledge_base", {"query": "nonexistent topic"})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("No knowledge base results found" in t for t in texts)


@pytest.mark.asyncio
async def test_get_knowledge_base_schema(mcp_client):
    mock_response = {
        "nodes": [{"name": "Paper", "properties": [{"name": "title", "type": "STRING"}]}],
        "relationships": [
            {
                "name": "CITES",
                "properties": [],
                "patterns": [{"from_label": "Paper", "to_label": "Paper"}],
            }
        ],
    }

    with patch.object(KnowledgeBaseService, "get_schema", return_value=mock_response):
        response = await mcp_client.call_tool("get_knowledge_base_schema", {})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("Paper" in t and "CITES" in t for t in texts)


@pytest.mark.asyncio
async def test_get_knowledge_base_overview(mcp_client):
    mock_response = {
        "total_papers": 120,
        "total_key_metrics": 543,
        "devices": [{"name": "Ring Resonator", "count": 40}],
        "materials": [{"name": "Silicon Nitride", "count": 55}],
    }

    with patch.object(KnowledgeBaseService, "get_overview", return_value=mock_response):
        response = await mcp_client.call_tool("get_knowledge_base_overview", {})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("Total papers: 120" in t and "Ring Resonator" in t and "Silicon Nitride" in t for t in texts)


@pytest.mark.asyncio
async def test_list_knowledge_base_papers(mcp_client):
    mock_response = {
        "items": [
            {
                "paper_id": "2301.07041",
                "title": "Low-loss ring resonators",
                "authors": ["A. Author"],
                "keyMetricCount": 3,
            }
        ],
        "total": 1,
        "page": 1,
        "page_size": 20,
        "total_pages": 1,
    }

    with patch.object(KnowledgeBaseService, "list_papers", return_value=mock_response):
        response = await mcp_client.call_tool("list_knowledge_base_papers", {})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("Low-loss ring resonators" in t and "2301.07041" in t for t in texts)


@pytest.mark.asyncio
async def test_list_knowledge_base_papers_no_results(mcp_client):
    mock_response = {"items": [], "total": 0, "page": 5, "page_size": 20, "total_pages": 1}

    with patch.object(KnowledgeBaseService, "list_papers", return_value=mock_response):
        response = await mcp_client.call_tool("list_knowledge_base_papers", {"page": 5})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("No papers found on page 5" in t for t in texts)


@pytest.mark.asyncio
async def test_knowledge_graph_read_renders_rows_as_a_table(mcp_client):
    mock_response = {
        "schema_kind": "table",
        "columns": ["name", "ce_dB", "bw_nm"],
        "rows": [
            {"name": "Apodized SOI grating coupler", "ce_dB": -0.8, "bw_nm": 38.8},
            {"name": "Curved LNOI grating coupler", "ce_dB": -3.9, "bw_nm": 90.0},
        ],
        "count": 2,
        "truncated": False,
    }

    with patch.object(KnowledgeBaseService, "execute_read", return_value=mock_response) as spy:
        response = await mcp_client.call_tool(
            "knowledge_graph_read",
            {"query": "MATCH (d:GratingCoupler) RETURN d.name AS name"},
        )

    spy.assert_called_once_with("MATCH (d:GratingCoupler) RETURN d.name AS name", None)
    text = "\n".join(c.text for c in response.content if hasattr(c, "text"))
    # Header, both rows and the count all have to survive the formatter: the whole point of
    # this tool over search_knowledge_base is that the caller gets every row, as a table.
    assert "name" in text and "ce_dB" in text and "bw_nm" in text
    assert "Apodized SOI grating coupler" in text
    assert "Curved LNOI grating coupler" in text
    assert "2 row(s)" in text
    assert response.structured_content == mock_response


@pytest.mark.asyncio
async def test_knowledge_graph_read_reports_server_side_truncation(mcp_client):
    """`truncated` is the endpoint's row cap. Swallowing it would read as a complete answer."""
    mock_response = {
        "schema_kind": "table",
        "columns": ["name"],
        "rows": [{"name": f"device {i}"} for i in range(3)],
        "count": 3,
        "truncated": True,
    }

    with patch.object(KnowledgeBaseService, "execute_read", return_value=mock_response):
        response = await mcp_client.call_tool("knowledge_graph_read", {"query": "MATCH (n) RETURN n.name AS name"})

    text = "\n".join(c.text for c in response.content if hasattr(c, "text"))
    assert "Truncated" in text


@pytest.mark.asyncio
async def test_knowledge_graph_read_no_rows(mcp_client):
    mock_response = {"schema_kind": "table", "columns": [], "rows": [], "count": 0, "truncated": False}

    with patch.object(KnowledgeBaseService, "execute_read", return_value=mock_response):
        response = await mcp_client.call_tool("knowledge_graph_read", {"query": "MATCH (n:Nope) RETURN n.name AS name"})

    text = "\n".join(c.text for c in response.content if hasattr(c, "text"))
    assert "no rows" in text.lower()


@pytest.mark.asyncio
async def test_knowledge_graph_read_passes_params_through(mcp_client):
    mock_response = {"schema_kind": "table", "columns": ["name"], "rows": [{"name": "SiN GC"}], "count": 1, "truncated": False}

    with patch.object(KnowledgeBaseService, "execute_read", return_value=mock_response) as spy:
        await mcp_client.call_tool(
            "knowledge_graph_read",
            {"query": "MATCH (d {name: $n}) RETURN d.name AS name", "params": {"n": "SiN GC"}},
        )

    spy.assert_called_once_with("MATCH (d {name: $n}) RETURN d.name AS name", {"n": "SiN GC"})
