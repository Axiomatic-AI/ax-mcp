"""Tests for the AxKnowledgeBase MCP server."""

from unittest.mock import patch

import httpx
import pytest
import pytest_asyncio
from fastmcp.client import Client

from axiomatic_mcp.servers.kb.server import mcp
from axiomatic_mcp.servers.kb.services.knowledge_base_service import KnowledgeBaseService
from axiomatic_mcp.shared.constants.api_constants import ApiRoutes

PDF_BYTES = b"%PDF-1.4\n%\xc7\xec\x8f\xa2\ntrailer\n<<>>\n%%EOF\n"


def _texts(response) -> str:
    return "\n".join(block.text for block in response.content if hasattr(block, "text"))


def _status_error(status_code: int, detail) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://api.example.com/neo4j/private/ingest")
    response = httpx.Response(status_code, json={"detail": detail}, request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


def _pdf(tmp_path, name: str = "paper.pdf", content: bytes = PDF_BYTES):
    path = tmp_path / name
    path.write_bytes(content)
    return path


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
        "knowledge_graph_read",
        "ingest_pdf_to_private_knowledge_base",
        "search_private_knowledge_base",
        "get_private_knowledge_base_overview",
        "private_knowledge_graph_read",
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
    """Regression: the formatter used to read total_papers/devices/materials, which the endpoint
    does not return, so every real response rendered as zeros."""
    mock_response = {"items": [{"label": "Passage", "count": 5000}, {"label": "Entity", "count": 1200}], "total": 6100}

    with patch.object(KnowledgeBaseService, "get_overview", return_value=mock_response):
        response = await mcp_client.call_tool("get_knowledge_base_overview", {})

    text = _texts(response)
    assert "Passage" in text and "5000" in text
    assert "Entity" in text and "1200" in text
    assert "6100" in text
    assert "Total papers:" not in text
    # The counts legitimately over-add, so the response has to say why.
    assert "once per label" in text


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


@pytest.mark.asyncio
async def test_knowledge_graph_read_flags_missing_provenance(mcp_client):
    """Cypher rows only carry what the query returned, so an uncited result set has to say so —
    otherwise the model presents graph numbers as sourced literature values."""
    uncited = {"schema_kind": "table", "columns": ["name", "ce_dB"], "rows": [{"name": "SiN GC", "ce_dB": -1.2}], "count": 1}
    cited = {
        "schema_kind": "table",
        "columns": ["name", "paper_id"],
        "rows": [{"name": "SiN GC", "paper_id": "2301.07041"}],
        "count": 1,
    }

    with patch.object(KnowledgeBaseService, "execute_read", return_value=uncited):
        response = await mcp_client.call_tool("knowledge_graph_read", {"query": "MATCH (n) RETURN n.name AS name"})
    assert "uncited" in "\n".join(c.text for c in response.content if hasattr(c, "text"))

    with patch.object(KnowledgeBaseService, "execute_read", return_value=cited):
        response = await mcp_client.call_tool("knowledge_graph_read", {"query": "MATCH (n) RETURN n.name AS name"})
    assert "uncited" not in "\n".join(c.text for c in response.content if hasattr(c, "text"))


@pytest.mark.asyncio
async def test_knowledge_graph_read_bounds_response_size(mcp_client):
    """The endpoint's row cap is not a size cap — 500 rows of passage text is megabytes. The
    table elides long cells and stops at a character budget; the structured result keeps all of it."""
    long_text = "x" * 5000
    mock_response = {
        "schema_kind": "table",
        "columns": ["paper_id", "text"],
        "rows": [{"paper_id": f"p{i}", "text": long_text} for i in range(50)],
        "count": 50,
    }

    with patch.object(KnowledgeBaseService, "execute_read", return_value=mock_response):
        response = await mcp_client.call_tool("knowledge_graph_read", {"query": "MATCH (p:Passage) RETURN p.text AS text"})

    text = "\n".join(c.text for c in response.content if hasattr(c, "text"))
    assert long_text not in text
    assert "Table stopped after" in text
    assert len(text) < 15_000
    assert response.structured_content["rows"][0]["text"] == long_text


# ── private graph: ingest ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_reports_what_was_extracted(mcp_client, tmp_path):
    path = _pdf(tmp_path)
    mock_response = {
        "paper_id": "hash-abc",
        "title": "Low-loss ring resonators",
        "already_present": False,
        "pdf_stored": True,
        "passages": 42,
        "entities": 17,
        "statements": 23,
    }

    with patch.object(KnowledgeBaseService, "private_ingest", return_value=mock_response) as spy:
        response = await mcp_client.call_tool("ingest_pdf_to_private_knowledge_base", {"file_path": str(path)})

    spy.assert_called_once_with("paper.pdf", PDF_BYTES, "", "")
    text = _texts(response)
    assert "hash-abc" in text and "Low-loss ring resonators" in text
    assert "42" in text and "17" in text and "23" in text
    # The paper is only in the private graph, so the model must be pointed at the right search tool.
    assert "search_private_knowledge_base" in text
    assert response.structured_content == mock_response


@pytest.mark.asyncio
async def test_ingest_passes_title_and_paper_id_through(mcp_client, tmp_path):
    path = _pdf(tmp_path)
    mock_response = {
        "paper_id": "mine-1",
        "title": "Mine",
        "already_present": False,
        "pdf_stored": True,
        "passages": 1,
        "entities": 1,
        "statements": 1,
    }

    with patch.object(KnowledgeBaseService, "private_ingest", return_value=mock_response) as spy:
        await mcp_client.call_tool(
            "ingest_pdf_to_private_knowledge_base",
            {"file_path": str(path), "title": "Mine", "paper_id": "mine-1"},
        )

    spy.assert_called_once_with("paper.pdf", PDF_BYTES, "Mine", "mine-1")


@pytest.mark.asyncio
async def test_ingest_explains_an_already_present_paper(mcp_client, tmp_path):
    """Every count is zero when the paper was already there. Rendered bare, that reads as an
    extraction that found nothing, and the model retries or reports failure."""
    path = _pdf(tmp_path)
    mock_response = {
        "paper_id": "hash-abc",
        "title": "Low-loss ring resonators",
        "already_present": True,
        "pdf_stored": True,
        "passages": 0,
        "entities": 0,
        "statements": 0,
    }

    with patch.object(KnowledgeBaseService, "private_ingest", return_value=mock_response):
        response = await mcp_client.call_tool("ingest_pdf_to_private_knowledge_base", {"file_path": str(path)})

    text = _texts(response)
    assert "already" in text.lower()
    assert "expected" in text.lower()


@pytest.mark.asyncio
async def test_ingest_warns_when_the_source_pdf_was_not_stored(mcp_client, tmp_path):
    """pdf_stored false is silently lossy: the paper is queryable but the PDF cannot be fetched
    again, and re-sending is what completes it."""
    path = _pdf(tmp_path)
    mock_response = {
        "paper_id": "hash-abc",
        "title": "Partly there",
        "already_present": False,
        "pdf_stored": False,
        "passages": 10,
        "entities": 2,
        "statements": 3,
    }

    with patch.object(KnowledgeBaseService, "private_ingest", return_value=mock_response):
        response = await mcp_client.call_tool("ingest_pdf_to_private_knowledge_base", {"file_path": str(path)})

    text = _texts(response)
    assert "did not finish uploading" in text
    assert "again" in text


@pytest.mark.asyncio
async def test_ingest_refuses_a_missing_file_without_calling_the_api(mcp_client, tmp_path):
    with patch.object(KnowledgeBaseService, "private_ingest") as spy:
        response = await mcp_client.call_tool(
            "ingest_pdf_to_private_knowledge_base",
            {"file_path": str(tmp_path / "nope.pdf")},
            raise_on_error=False,
        )

    assert response.is_error is True
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_ingest_refuses_a_non_pdf_without_calling_the_api(mcp_client, tmp_path):
    """The extension can lie, so the bytes are sniffed. Worth failing in milliseconds rather than
    after a request that can run for minutes."""
    path = _pdf(tmp_path, name="actually_a_png.pdf", content=b"\x89PNG\r\n\x1a\n" + b"\x00" * 40)

    with patch.object(KnowledgeBaseService, "private_ingest") as spy:
        response = await mcp_client.call_tool(
            "ingest_pdf_to_private_knowledge_base",
            {"file_path": str(path)},
            raise_on_error=False,
        )

    assert response.is_error is True
    assert "PDF" in _texts(response)
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_ingest_refuses_an_empty_file_without_calling_the_api(mcp_client, tmp_path):
    path = _pdf(tmp_path, content=b"")

    with patch.object(KnowledgeBaseService, "private_ingest") as spy:
        response = await mcp_client.call_tool(
            "ingest_pdf_to_private_knowledge_base",
            {"file_path": str(path)},
            raise_on_error=False,
        )

    assert response.is_error is True
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_ingest_surfaces_api_errors_as_a_tool_error(mcp_client, tmp_path):
    path = _pdf(tmp_path)

    with patch.object(KnowledgeBaseService, "private_ingest", side_effect=_status_error(504, "timed out")):
        response = await mcp_client.call_tool(
            "ingest_pdf_to_private_knowledge_base",
            {"file_path": str(path)},
            raise_on_error=False,
        )

    assert response.is_error is True
    assert "Failed to ingest the PDF" in _texts(response)


@pytest.mark.asyncio
async def test_private_search_surfaces_api_errors_as_a_tool_error(mcp_client):
    with patch.object(KnowledgeBaseService, "private_search", side_effect=_status_error(403, "no private graph")):
        response = await mcp_client.call_tool("search_private_knowledge_base", {"query": "anything"}, raise_on_error=False)

    assert response.is_error is True
    assert "Failed to search the private knowledge base" in _texts(response)


# ── private graph: reads ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_private_search_reuses_the_citation_formatter(mcp_client):
    mock_response = {
        "query": "our ring resonator",
        "results": [
            {
                "text": "Internal measurements put the Q factor at 2e6.",
                "score": 0.91,
                "metadata": {"paper_id": "internal-1", "paper_title": "Internal report"},
            }
        ],
        "count": 1,
    }

    with patch.object(KnowledgeBaseService, "private_search", return_value=mock_response) as spy:
        response = await mcp_client.call_tool("search_private_knowledge_base", {"query": "our ring resonator", "limit": 3})

    spy.assert_called_once_with("our ring resonator", 3)
    text = _texts(response)
    assert "Internal report" in text and "0.910" in text
    assert response.structured_content == mock_response


@pytest.mark.asyncio
async def test_private_graph_read_renders_rows_and_passes_params(mcp_client):
    mock_response = {
        "schema_kind": "table",
        "columns": ["name", "paper_id"],
        "rows": [{"name": "Our GC", "paper_id": "internal-1"}],
        "count": 1,
        "truncated": False,
    }

    with patch.object(KnowledgeBaseService, "private_execute_read", return_value=mock_response) as spy:
        response = await mcp_client.call_tool(
            "private_knowledge_graph_read",
            {"query": "MATCH (d {name: $n}) RETURN d.name AS name", "params": {"n": "Our GC"}},
        )

    spy.assert_called_once_with("MATCH (d {name: $n}) RETURN d.name AS name", {"n": "Our GC"})
    text = _texts(response)
    assert "Our GC" in text and "internal-1" in text
    assert "1 row(s)" in text
    # Provenance column present, so the shared formatter must not flag it.
    assert "uncited" not in text


@pytest.mark.asyncio
async def test_private_overview_renders_label_counts(mcp_client):
    mock_response = {"items": [{"label": "Document", "count": 3}], "total": 812}

    with patch.object(KnowledgeBaseService, "private_overview", return_value=mock_response) as spy:
        response = await mcp_client.call_tool("get_private_knowledge_base_overview", {})

    spy.assert_called_once_with()
    text = _texts(response)
    assert "Document" in text and "3" in text and "812" in text


@pytest.mark.asyncio
async def test_private_overview_on_an_empty_graph(mcp_client):
    """A brand new private graph is the common first call — it must not render as a broken table."""
    with patch.object(KnowledgeBaseService, "private_overview", return_value={"items": [], "total": 0}):
        response = await mcp_client.call_tool("get_private_knowledge_base_overview", {})

    assert "no labelled nodes" in _texts(response)


def test_private_route_constants():
    """The contract is hand-maintained, so the paths are pinned here rather than trusted."""
    assert ApiRoutes.KNOWLEDGE_BASE_PRIVATE_SEARCH == "/neo4j/private/search"
    assert ApiRoutes.KNOWLEDGE_BASE_PRIVATE_OVERVIEW == "/neo4j/private/overview"
    assert ApiRoutes.KNOWLEDGE_BASE_PRIVATE_EXECUTE_READ == "/neo4j/private/execute-read"
    assert ApiRoutes.KNOWLEDGE_BASE_PRIVATE_INGEST == "/neo4j/private/ingest"
    assert not hasattr(ApiRoutes, "KNOWLEDGE_BASE_LIST_PAPERS")
