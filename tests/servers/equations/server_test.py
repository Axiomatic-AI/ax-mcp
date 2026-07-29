"""Tests for the AxEquationExplorer MCP server."""

import base64
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastmcp.client import Client

from axiomatic_mcp.servers.equations.server import mcp
from axiomatic_mcp.servers.equations.services.equations_service import EquationsService
from axiomatic_mcp.shared.constants.api_constants import ApiRoutes

SERVICE_CLIENT = "axiomatic_mcp.servers.equations.services.equations_service.AxiomaticAPIClient"
DERIVE_RESPONSE = {"code": "E = p**2 / (2 * m)", "explanation": "derived from momentum", "status": "SUCCESS"}


def _mock_client(mock_client_cls, response):
    client = mock_client_cls.return_value.__enter__.return_value
    client.post.return_value = response
    return client


def test_routes_point_at_expressions_endpoints():
    assert ApiRoutes.EQUATIONS_DERIVE == "/expressions/derive"
    assert ApiRoutes.EQUATIONS_CHECK == "/expressions/check"


def test_derive_with_markdown_sends_json_body():
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, DERIVE_RESPONSE)
        result = EquationsService().derive("derive E from p", markdown="# doc")

    client.post.assert_called_once_with(
        "/expressions/derive",
        data={"task": "derive E from p", "markdown": "# doc"},
    )
    assert result == DERIVE_RESPONSE


def test_derive_with_pdf_sends_base64_json_body():
    pdf_bytes = b"%PDF-1.4 fake pdf"
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, DERIVE_RESPONSE)
        EquationsService().derive("derive E", pdf_bytes=pdf_bytes)

    client.post.assert_called_once_with(
        "/expressions/derive",
        data={"task": "derive E", "pdf_base64": base64.b64encode(pdf_bytes).decode("ascii")},
    )


def test_check_with_markdown_sends_json_body():
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, DERIVE_RESPONSE)
        EquationsService().check("is E=mc^2 correct?", markdown="# doc")

    client.post.assert_called_once_with(
        "/expressions/check",
        data={"task": "is E=mc^2 correct?", "markdown": "# doc"},
    )


@pytest.mark.parametrize("kwargs", [{}, {"markdown": "# doc", "pdf_bytes": b"%PDF"}])
def test_exactly_one_document_source_required(kwargs):
    # Test _build_payload directly: derive() would also raise ValueError from the
    # AxiomaticAPIClient constructor when AXIOMATIC_API_KEY is unset (e.g. in CI),
    # which would make a derive()-based test pass for the wrong reason.
    with pytest.raises(ValueError, match="exactly one"):
        EquationsService()._build_payload("task", **kwargs)


@pytest_asyncio.fixture
async def mcp_client():
    async with Client(transport=mcp) as client:
        yield client


@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    tools = await mcp_client.list_tools()
    tool_names = {t.name for t in tools}
    assert {"find_functional_form", "check_equation"} <= tool_names


@pytest.mark.asyncio
async def test_find_functional_form_with_inline_markdown(mcp_client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch.object(EquationsService, "derive", return_value=DERIVE_RESPONSE) as mock_derive:
        response = await mcp_client.call_tool(
            "find_functional_form",
            {"document": "Momentum is $p = m v$ and energy is $E = \\frac{1}{2} m v^2$.", "task": "express E via p"},
        )

    mock_derive.assert_called_once_with(
        task="express E via p",
        markdown="Momentum is $p = m v$ and energy is $E = \\frac{1}{2} m v^2$.",
        pdf_bytes=None,
    )
    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("derived from momentum" in t for t in texts)
    assert (tmp_path / "expression_code.py").read_text(encoding="utf-8") == DERIVE_RESPONSE["code"]


@pytest.mark.asyncio
async def test_check_equation_with_pdf_path_passes_raw_bytes(mcp_client, tmp_path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 fake pdf")

    with patch.object(EquationsService, "check", return_value=DERIVE_RESPONSE) as mock_check:
        await mcp_client.call_tool("check_equation", {"document": str(pdf_path), "task": "check eq 3"})

    mock_check.assert_called_once_with(task="check eq 3", markdown=None, pdf_bytes=b"%PDF-1.4 fake pdf")
