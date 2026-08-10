"""Tests for the AxPde MCP server."""

from unittest.mock import patch

import pytest
import pytest_asyncio
from fastmcp.client import Client

from axiomatic_mcp.servers.pde.server import mcp
from axiomatic_mcp.servers.pde.services.pde_service import PdeService
from axiomatic_mcp.shared.constants.api_constants import ApiRoutes

SERVICE_CLIENT = "axiomatic_mcp.servers.pde.services.pde_service.AxiomaticAPIClient"

HEAT_OPERATOR = (
    "def pde_operator(fields, vars_dict):\n" '    u = fields["u"]\n' '    return sp.diff(u, vars_dict["t"]) - sp.diff(u, vars_dict["x"], 2)'
)
HEAT_EQUATIONS = [{"name": "pde", "operator_code": HEAT_OPERATOR}]
HEAT_SOLUTION = {"u": "sin(pi*x)*exp(-t)"}
HEAT_SOURCE = {"pde": "(-1 + pi**2)*exp(-t)*sin(pi*x)"}


def _mock_client(mock_client_cls, response):
    client = mock_client_cls.return_value.__enter__.return_value
    client.post.return_value = response
    return client


def test_routes_point_at_pde_endpoints():
    assert ApiRoutes.PDE_PARSE == "/numerics/pde/parse"
    assert ApiRoutes.PDE_DERIVE_SOURCE == "/numerics/pde/derive-source"
    assert ApiRoutes.PDE_VERIFY == "/numerics/pde/verify"


def test_parse_sends_json_body():
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, {"success": True, "spec": {}})
        PdeService().parse("Heat equation u_t = u_xx on [0,1]")

    client.post.assert_called_once_with(
        "/numerics/pde/parse",
        data={"description": "Heat equation u_t = u_xx on [0,1]"},
    )


def test_derive_source_sends_json_body():
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, {"success": True, "source_exprs": HEAT_SOURCE})
        PdeService().derive_source(HEAT_EQUATIONS, HEAT_SOLUTION, ["x", "t"])

    client.post.assert_called_once_with(
        "/numerics/pde/derive-source",
        data={
            "equations": HEAT_EQUATIONS,
            "solution_exprs": HEAT_SOLUTION,
            "variables": ["x", "t"],
        },
    )


def test_verify_defaults_optional_fields():
    """Omitted BCs/domain/unknowns must become [], {} and ["u"] — not None, which the API rejects."""
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, {"passed": True})
        PdeService().verify(HEAT_EQUATIONS, HEAT_SOLUTION, HEAT_SOURCE, ["x", "t"])

    client.post.assert_called_once_with(
        "/numerics/pde/verify",
        data={
            "equations": HEAT_EQUATIONS,
            "solution_exprs": HEAT_SOLUTION,
            "source_exprs": HEAT_SOURCE,
            "variables": ["x", "t"],
            "boundary_conditions": [],
            "domain": {},
            "unknowns": ["u"],
        },
    )


@pytest_asyncio.fixture
async def mcp_client():
    async with Client(transport=mcp) as client:
        yield client


@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    tools = await mcp_client.list_tools()
    tool_names = {t.name for t in tools}
    assert {"parse_pde", "derive_source", "verify_solution"} <= tool_names


@pytest.mark.asyncio
async def test_parse_backend_error(mcp_client):
    mock_response = {"success": False, "spec": None, "error": "PDE parse produced no equations / operators."}

    with patch.object(PdeService, "parse", return_value=mock_response):
        response = await mcp_client.call_tool("parse_pde", {"description": "something unparseable"})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("no equations" in t for t in texts)


@pytest.mark.asyncio
async def test_parse_success_surfaces_operator_code(mcp_client):
    mock_response = {
        "success": True,
        "spec": {
            "name": "heat_1d",
            "pde_latex": r"u_t = u_{xx}",
            "domain": {"type": "interval", "x_min": 0, "x_max": 1},
            "variables": ["x", "t"],
            "unknowns": ["u"],
            "equations": HEAT_EQUATIONS,
            "boundary_conditions": [{"label": "x=0", "type": "dirichlet", "subs": {"x": 0}, "value": "0"}],
        },
        "compile_results": {"pde": {"compiled": True}},
    }

    with patch.object(PdeService, "parse", return_value=mock_response):
        response = await mcp_client.call_tool("parse_pde", {"description": "1D heat equation on [0,1]"})

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("heat_1d" in t for t in texts)
    assert any("sp.diff" in t for t in texts)


@pytest.mark.asyncio
async def test_derive_source_renders_source_terms(mcp_client):
    mock_response = {"success": True, "source_exprs": HEAT_SOURCE, "error": None}

    with patch.object(PdeService, "derive_source", return_value=mock_response) as mock_derive:
        response = await mcp_client.call_tool(
            "derive_source",
            {"equations": HEAT_EQUATIONS, "solution_exprs": HEAT_SOLUTION, "variables": ["x", "t"]},
        )

    mock_derive.assert_called_once_with(HEAT_EQUATIONS, HEAT_SOLUTION, ["x", "t"])
    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("(-1 + pi**2)*exp(-t)*sin(pi*x)" in t for t in texts)


@pytest.mark.asyncio
async def test_verify_success(mcp_client):
    mock_response = {
        "passed": True,
        "pde_residual_zero": True,
        "bcs_satisfied": True,
        "equation_diagnostics": {"pde": {"passed": True, "residual": "0"}},
        "bc_diagnostics": {"x=0": {"passed": True, "residual": "0"}},
        "message": "VERIFIED: All equations and boundary conditions satisfied.",
    }

    with patch.object(PdeService, "verify", return_value=mock_response):
        response = await mcp_client.call_tool(
            "verify_solution",
            {
                "equations": HEAT_EQUATIONS,
                "solution_exprs": HEAT_SOLUTION,
                "source_exprs": HEAT_SOURCE,
                "variables": ["x", "t"],
            },
        )

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("VERIFIED" in t for t in texts)


@pytest.mark.asyncio
async def test_verify_failure_surfaces_diagnostics(mcp_client):
    """A failed verification is a legitimate result: it must come back as content, not raise."""
    mock_response = {
        "passed": False,
        "pde_residual_zero": False,
        "bcs_satisfied": True,
        "equation_diagnostics": {"pde": {"passed": False, "residual": "(pi**2 - 1)*exp(-t)*sin(pi*x)"}},
        "bc_diagnostics": {},
        "message": "FAILED: Equation residuals nonzero: ['pde']",
    }

    with patch.object(PdeService, "verify", return_value=mock_response):
        response = await mcp_client.call_tool(
            "verify_solution",
            {
                "equations": HEAT_EQUATIONS,
                "solution_exprs": HEAT_SOLUTION,
                "source_exprs": {"pde": "0"},
                "variables": ["x", "t"],
            },
        )

    assert not response.is_error
    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("NOT VERIFIED" in t for t in texts)
    assert any("(pi**2 - 1)*exp(-t)*sin(pi*x)" in t for t in texts)


@pytest.mark.asyncio
async def test_verify_failing_bc_surfaces_label(mcp_client):
    mock_response = {
        "passed": False,
        "pde_residual_zero": True,
        "bcs_satisfied": False,
        "equation_diagnostics": {"pde": {"passed": True, "residual": "0"}},
        "bc_diagnostics": {"periodic": {"passed": False, "residual": "periodic BC could not be verified: no domain provided"}},
        "message": "FAILED: BCs failed: ['periodic']",
    }

    with patch.object(PdeService, "verify", return_value=mock_response):
        response = await mcp_client.call_tool(
            "verify_solution",
            {
                "equations": HEAT_EQUATIONS,
                "solution_exprs": HEAT_SOLUTION,
                "source_exprs": HEAT_SOURCE,
                "variables": ["x", "t"],
                "boundary_conditions": [{"label": "periodic", "type": "periodic"}],
            },
        )

    texts = [c.text for c in response.content if hasattr(c, "text")]
    assert any("could not be verified" in t for t in texts)


@pytest.mark.asyncio
async def test_verify_transport_failure_raises(mcp_client):
    """Unlike a failed verification, a transport error must surface as a tool error."""
    with patch.object(PdeService, "verify", side_effect=RuntimeError("connection refused")):
        response = await mcp_client.call_tool(
            "verify_solution",
            {
                "equations": HEAT_EQUATIONS,
                "solution_exprs": HEAT_SOLUTION,
                "source_exprs": HEAT_SOURCE,
                "variables": ["x", "t"],
            },
            raise_on_error=False,
        )

    assert response.is_error
