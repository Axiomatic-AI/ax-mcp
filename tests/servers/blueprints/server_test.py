"""Tests for the AxBlueprints MCP server."""

from unittest.mock import patch

import httpx
import pytest
import pytest_asyncio
from fastmcp.client import Client

from axiomatic_mcp.servers.blueprints.server import mcp
from axiomatic_mcp.servers.blueprints.services.blueprint_service import BlueprintService
from axiomatic_mcp.shared.constants.api_constants import ApiRoutes

MMI_ITEM = {
    "id": "photonics/mmi",
    "domain": "photonics",
    "name": "mmi",
    "component_type": "mmi",
    "status": "scaffolded",
    "version": 0,
    "n_optical": 4,
    "n_electrical": 0,
    "available_sections": ["manifest", "state", "validity", "source", "decisions", "eval", "verification"],
}

MMI_MANIFEST = {
    "id": "photonics/mmi",
    "status": "scaffolded",
    "n_optical": 4,
    "n_electrical": 0,
    "reflective": True,
    "passive": True,
    "reciprocal": True,
    "requires_profile": True,
    "ports": [
        {"name": "o1", "direction": "input"},
        {"name": "o3", "direction": "output"},
    ],
    "port_map": {"o1": "input left"},
    "modes": [{"name": "TE0", "dispersion_from": "profile"}],
    "parameters": [{"name": "length_um", "units": "um", "description": "Physical multimode-section length L."}],
    "depends_on": [],
    "verified_at": None,
    "budgets": {"sigma_max": 1.0},
}

STATE_MD = "# State\n\nstatus: scaffolded\nsince: 2026-09-08\n"


def _texts(response) -> str:
    return "\n".join(block.text for block in response.content if hasattr(block, "text"))


def _status_error(status_code: int, detail) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://api.example.com/blueprints/photonics/nope")
    response = httpx.Response(status_code, json={"detail": detail}, request=request)
    return httpx.HTTPStatusError(f"error - Response: {response.text}", request=request, response=response)


@pytest_asyncio.fixture
async def mcp_client():
    async with Client(transport=mcp) as client:
        yield client


@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    tools = await mcp_client.list_tools()
    assert {"list_blueprints", "get_blueprint"} <= {t.name for t in tools}


@pytest.mark.asyncio
async def test_list_blueprints_renders_the_catalog(mcp_client):
    y_junction = {**MMI_ITEM, "id": "photonics/y_junction", "name": "y_junction", "component_type": "y_junction", "n_optical": 3}
    mock_response = {"items": [MMI_ITEM, y_junction], "total": 2}

    with patch.object(BlueprintService, "list_blueprints", return_value=mock_response) as spy:
        response = await mcp_client.call_tool("list_blueprints", {})

    spy.assert_called_once_with(None, None)
    text = _texts(response)
    assert "2 blueprint(s)" in text
    assert "photonics/mmi" in text and "photonics/y_junction" in text
    assert "4 optical / 0 electrical" in text
    assert "sections: manifest, state, validity" in text
    assert response.structured_content == mock_response


@pytest.mark.asyncio
async def test_list_blueprints_flags_unverified_entries(mcp_client):
    """Every blueprint is scaffolded today; the planner must not read the catalog as validated."""
    verified = {**MMI_ITEM, "id": "photonics/eam", "status": "verified"}

    with patch.object(BlueprintService, "list_blueprints", return_value={"items": [MMI_ITEM, verified], "total": 2}):
        response = await mcp_client.call_tool("list_blueprints", {})

    text = _texts(response)
    assert "scaffolded (NOT verified)" in text
    assert "verified (NOT verified)" not in text
    assert "1 of 2 are not verified" in text


@pytest.mark.asyncio
async def test_list_blueprints_passes_filters_through(mcp_client):
    with patch.object(BlueprintService, "list_blueprints", return_value={"items": [], "total": 0}) as spy:
        response = await mcp_client.call_tool("list_blueprints", {"domain": "photonics", "status": "verified"})

    spy.assert_called_once_with("photonics", "verified")
    assert "No blueprints match" in _texts(response)


@pytest.mark.asyncio
async def test_get_blueprint_splits_the_id_and_uses_server_default_sections(mcp_client):
    mock_response = {**MMI_ITEM, "manifest": MMI_MANIFEST, "sections": {"state": STATE_MD}}

    with patch.object(BlueprintService, "get_blueprint", return_value=mock_response) as spy:
        response = await mcp_client.call_tool("get_blueprint", {"blueprint_id": "photonics/mmi"})

    spy.assert_called_once_with("photonics", "mmi", None)
    text = _texts(response)
    assert "scaffolded (NOT verified)" in text
    # Manifest summary: ports (with their port_map description), modes, parameters.
    assert "o1 (input, optical): input left" in text
    assert "Modes: TE0" in text
    assert "length_um [um]: Physical multimode-section length L." in text
    assert "Verified at: never" in text
    # Requested markdown in full; the rest named so the agent knows it can ask.
    assert STATE_MD in text
    assert "Not fetched: validity, source, decisions, eval, verification" in text
    assert response.structured_content == mock_response


@pytest.mark.asyncio
async def test_get_blueprint_passes_sections_through(mcp_client):
    mock_response = {**MMI_ITEM, "manifest": None, "sections": {"validity": "# Validity\n\n1500-1600 nm", "source": "# Source\n\nSoldano 1995"}}

    with patch.object(BlueprintService, "get_blueprint", return_value=mock_response) as spy:
        response = await mcp_client.call_tool("get_blueprint", {"blueprint_id": "photonics/mmi", "sections": ["validity", "source"]})

    spy.assert_called_once_with("photonics", "mmi", ["validity", "source"])
    text = _texts(response)
    assert "1500-1600 nm" in text and "Soldano 1995" in text
    assert "Manifest summary" not in text
    assert "Not fetched: manifest, state, decisions, eval, verification" in text


@pytest.mark.asyncio
async def test_get_blueprint_rejects_an_invalid_section_without_calling_the_api(mcp_client):
    with patch.object(BlueprintService, "get_blueprint") as spy:
        response = await mcp_client.call_tool(
            "get_blueprint",
            {"blueprint_id": "photonics/mmi", "sections": ["physics"]},
            raise_on_error=False,
        )

    assert response.is_error is True
    spy.assert_not_called()


@pytest.mark.parametrize("blueprint_id", ["mmi", "photonics/", "/mmi", "photonics/mmi/extra"])
@pytest.mark.asyncio
async def test_get_blueprint_rejects_a_malformed_id_without_calling_the_api(mcp_client, blueprint_id):
    with patch.object(BlueprintService, "get_blueprint") as spy:
        response = await mcp_client.call_tool("get_blueprint", {"blueprint_id": blueprint_id}, raise_on_error=False)

    assert response.is_error is True
    assert "list_blueprints" in _texts(response)
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_get_blueprint_surfaces_a_404_with_the_available_ids(mcp_client):
    """The API's 404 lists the ids that exist; that list is what lets the agent recover."""
    error = _status_error(404, "Blueprint 'photonics/nope' not found. Available: photonics/mmi, photonics/y_junction")

    with patch.object(BlueprintService, "get_blueprint", side_effect=error):
        response = await mcp_client.call_tool("get_blueprint", {"blueprint_id": "photonics/nope"}, raise_on_error=False)

    assert response.is_error is True
    text = _texts(response)
    assert "Failed to get blueprint 'photonics/nope'" in text
    assert "photonics/y_junction" in text


@pytest.mark.asyncio
async def test_list_blueprints_surfaces_api_errors_as_a_tool_error(mcp_client):
    with patch.object(BlueprintService, "list_blueprints", side_effect=_status_error(401, "Not authenticated")):
        response = await mcp_client.call_tool("list_blueprints", {}, raise_on_error=False)

    assert response.is_error is True
    assert "Failed to list blueprints" in _texts(response)


def test_service_sends_sections_as_repeated_query_params():
    """FastAPI reads a list query param as a repeated key, not a comma-joined string."""
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = request.url
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)
    original_client = httpx.Client

    with (
        patch.dict("os.environ", {"AXIOMATIC_API_KEY": "test", "AXIOMATIC_API_URL": "https://api.example.com"}),
        patch("httpx.Client", lambda **kwargs: original_client(transport=transport, **kwargs)),
    ):
        BlueprintService().get_blueprint("photonics", "mmi", ["manifest", "validity"])

    assert captured["url"].path == "/blueprints/photonics/mmi"
    assert captured["url"].params.get_list("sections") == ["manifest", "validity"]


def test_route_constants():
    """The contract is hand-maintained, so the paths are pinned here rather than trusted."""
    assert ApiRoutes.BLUEPRINTS_LIST == "/blueprints"
    assert ApiRoutes.BLUEPRINTS_GET == "/blueprints/{domain}/{name}"
