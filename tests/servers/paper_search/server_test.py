"""Tests for the AxPaperSearch MCP server."""

from unittest.mock import patch

import pytest
import pytest_asyncio
from fastmcp.client import Client

from axiomatic_mcp.servers.paper_search.server import mcp
from axiomatic_mcp.servers.paper_search.services.paper_search_service import PaperSearchService


@pytest_asyncio.fixture
async def mcp_client():
    async with Client(transport=mcp) as client:
        yield client


@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    tools = await mcp_client.list_tools()
    tool_names = {t.name for t in tools}
    assert {"search_arxiv", "search_openalex"} <= tool_names


@pytest.mark.asyncio
async def test_search_arxiv_returns_pdf_link(mcp_client):
    mock_response = {
        "papers": [
            {
                "arxiv_id": "2301.07041v1",
                "title": "Low-loss ring resonators",
                "summary": "We report Q factors of 1e6 in silicon nitride ring resonators.",
                "authors": ["A. Researcher", "B. Scientist"],
                "categories": ["physics.optics"],
                "abs_url": "https://arxiv.org/abs/2301.07041v1",
                "pdf_url": "https://arxiv.org/pdf/2301.07041v1",
            }
        ],
        "total_results": 1,
        "query": "ring resonator loss",
    }

    with patch.object(PaperSearchService, "search_arxiv", return_value=mock_response):
        response = await mcp_client.call_tool("search_arxiv", {"query": "ring resonator loss"})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("Low-loss ring resonators" in t and "arxiv.org/pdf" in t for t in texts)


@pytest.mark.asyncio
async def test_search_arxiv_no_results(mcp_client):
    mock_response = {"papers": [], "total_results": 0, "query": "nonexistent topic"}

    with patch.object(PaperSearchService, "search_arxiv", return_value=mock_response):
        response = await mcp_client.call_tool("search_arxiv", {"query": "nonexistent topic"})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("No arXiv results found" in t for t in texts)


@pytest.mark.asyncio
async def test_search_openalex_surfaces_citation_count(mcp_client):
    mock_response = {
        "results": [
            {
                "id": "W123",
                "title": "Low-loss ring resonators",
                "doi": "10.1000/abc",
                "publication_date": "2023-01-01",
                "type": "article",
                "open_access": True,
                "cited_by_count": 42,
                "authors": [{"name": "A. Researcher"}],
            }
        ]
    }

    with patch.object(PaperSearchService, "search_openalex", return_value=mock_response):
        response = await mcp_client.call_tool("search_openalex", {"query": "ring resonator loss"})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("cited 42 times" in t and "open access" in t for t in texts)
