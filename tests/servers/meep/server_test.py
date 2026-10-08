"""Tests for the AxMeep MCP server."""

import base64
import io
import json
from unittest.mock import patch

import httpx
import numpy as np
import pytest
import pytest_asyncio
from fastmcp.client import Client

from axiomatic_mcp.servers.meep import server as meep_server
from axiomatic_mcp.servers.meep.server import mcp
from axiomatic_mcp.servers.meep.services.meep_service import MeepService
from axiomatic_mcp.shared.constants.api_constants import ApiRoutes

SERVICE_CLIENT = "axiomatic_mcp.servers.meep.services.meep_service.AxiomaticAPIClient"

# A real 1x1 PNG, so the magic-byte check and the image encoder both see valid input.
PNG_BYTES = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==")
PNG_B64 = base64.b64encode(PNG_BYTES).decode()


def _npy_b64(arr: np.ndarray) -> str:
    buffer = io.BytesIO()
    np.save(buffer, arr, allow_pickle=False)
    return base64.b64encode(buffer.getvalue()).decode()


def _npz_b64(**arrays: np.ndarray) -> str:
    buffer = io.BytesIO()
    np.savez(buffer, **arrays)
    return base64.b64encode(buffer.getvalue()).decode()


def _finding(
    kind: str = "courant_unstable",
    *,
    source: str = "computed",
    suggestion: str = "Lower the Courant factor to 1.0 or below.",
    detail: dict | None = None,
) -> dict:
    return {
        "kind": kind,
        "passed": False,
        "source": source,
        "not_applicable": [],
        "diverged": kind in {"courant_unstable", "diverged"},
        "final_decay_value": None,
        "shutoff_target": None,
        "engine_warnings": [],
        "detail": detail or {"courant": 1.2, "limit": 1.0},
        "suggestion": suggestion,
    }


def _results(
    exports: dict,
    console_output: str = "meep finished\n",
    failed_objects: dict | None = None,
    *,
    execution_status: str = "completed",
    diagnosis: dict | None = None,
    setup_findings: list[dict] | None = None,
) -> dict:
    return {
        "task_id": "job-1",
        "execution_status": execution_status,
        "console_output": console_output,
        "exports": exports,
        "failed_objects": failed_objects or {},
        "diagnosis": diagnosis,
        "setup_findings": setup_findings or [],
    }


def _mock_client(mock_client_cls, response):
    client = mock_client_cls.return_value.__enter__.return_value
    client.post.return_value = response
    client.get.return_value = response
    return client


def _status_error(status_code: int, body) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://api.example.com/numerics/meep/execute")
    response = httpx.Response(status_code, json=body, request=request)
    return httpx.HTTPStatusError("error", request=request, response=response)


def _texts(response) -> list[str]:
    return [block.text for block in response.content if hasattr(block, "text")]


def _blob(response) -> str:
    return "\n".join(_texts(response))


@pytest_asyncio.fixture
async def mcp_client():
    async with Client(transport=mcp) as client:
        yield client


@pytest_asyncio.fixture
async def fast_poll(monkeypatch):
    """Shrink the poll interval so wait-loop tests do not really sleep 5 s at a time."""
    monkeypatch.setattr(meep_server, "_WAIT_POLL_INTERVAL_SECONDS", 0.01)


# ── routes and registration ──────────────────────────────────────────────────


def test_routes_point_at_meep_endpoints():
    assert ApiRoutes.MEEP_WRITE_CODE == "/numerics/meep/write-code"
    assert ApiRoutes.MEEP_EXECUTE == "/numerics/meep/execute"
    assert ApiRoutes.MEEP_EXECUTE_STATUS == "/numerics/meep/execute/status/{task_id}"
    assert ApiRoutes.MEEP_EXECUTE_RESULTS == "/numerics/meep/execute/results/{task_id}"


@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    tools = await mcp_client.list_tools()
    tool_names = {t.name for t in tools}
    assert {"generate_code", "execute_code", "get_simulation_status", "get_results"} <= tool_names


@pytest.mark.asyncio
async def test_tools_publish_output_schemas(mcp_client):
    tools = {t.name: t for t in await mcp_client.list_tools()}
    for name in ("generate_code", "execute_code", "get_simulation_status", "get_results"):
        schema = tools[name].output_schema
        assert schema["type"] == "object"
        # No "required": both the success shape and the failure shape must validate, and
        # fastmcp enforces the declared schema client-side.
        assert "required" not in schema


@pytest.mark.asyncio
async def test_get_results_schema_describes_verification_fields(mcp_client):
    tools = {t.name: t for t in await mcp_client.list_tools()}
    properties = tools["get_results"].output_schema["properties"]

    assert {"execution_status", "diagnosis", "setup_findings", "checks_path"} <= properties.keys()


@pytest.mark.asyncio
async def test_structured_content_survives_output_schema(mcp_client):
    """The declared schema must not strip fields it does not name — chaining relies on the full dict."""
    response_body = {"code": "import meep", "explanation": "ok", "error": None, "undeclared_future_field": "kept"}

    with patch.object(MeepService, "write_code", return_value=response_body):
        response = await mcp_client.call_tool("generate_code", {"problem_description": "a waveguide"})

    assert response.structured_content == response_body


# ── service layer ────────────────────────────────────────────────────────────


def test_write_code_sends_json_body():
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, {"code": "c", "explanation": "e", "error": None})
        MeepService().write_code("a bend", previous_code="old", previous_error="trace")

    client.post.assert_called_once_with(
        "/numerics/meep/write-code",
        data={"problem_description": "a bend", "previous_code": "old", "previous_error": "trace"},
    )


def test_execute_code_sends_json_body():
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, {"task_id": "job-1"})
        MeepService().execute_code("import meep as mp")

    client.post.assert_called_once_with("/numerics/meep/execute", data={"code": "import meep as mp"})


def test_status_and_results_interpolate_task_id():
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, {"task_id": "job-1", "status": "running"})
        MeepService().get_status("job-1")
    client.get.assert_called_once_with("/numerics/meep/execute/status/job-1")

    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, {"task_id": "job-1", "exports": {}})
        MeepService().get_results("job-1")
    client.get.assert_called_once_with("/numerics/meep/execute/results/job-1")


def test_actionable_http_error_becomes_failure_dict():
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = mock_client_cls.return_value.__enter__.return_value
        client.post.side_effect = _status_error(400, {"detail": {"error_type": "no_exports", "message": "no export() call", "lineno": None}})
        result = MeepService().execute_code("print(1)")

    assert result["success"] is False
    assert result["error_type"] == "no_exports"
    assert result["status_code"] == 400
    assert result["lineno"] is None


def test_string_detail_is_normalized():
    """is_playground_user_guard returns {"detail": "Not authorized"} — a str, not a dict."""
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = mock_client_cls.return_value.__enter__.return_value
        client.post.side_effect = _status_error(403, {"detail": "Not authorized"})
        result = MeepService().execute_code("import meep")

    assert result["success"] is False
    assert result["status_code"] == 403
    assert result["error"] == "Not authorized"
    assert result["error_type"] == "http_error"


def test_non_actionable_http_error_is_reraised():
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = mock_client_cls.return_value.__enter__.return_value
        client.post.side_effect = _status_error(500, {"detail": "boom"})
        with pytest.raises(httpx.HTTPStatusError):
            MeepService().execute_code("import meep")


# ── generate_code ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_code_success(mcp_client):
    body = {"code": "import meep as mp\nexport('x', 1)", "explanation": "Builds a waveguide.", "error": None}

    with patch.object(MeepService, "write_code", return_value=body):
        response = await mcp_client.call_tool("generate_code", {"problem_description": "a waveguide"})

    blob = _blob(response)
    assert "Builds a waveguide." in blob
    assert "```python" in blob
    assert "execute_code" in blob


@pytest.mark.asyncio
async def test_generate_code_iteration_limit_advises_narrowing(mcp_client):
    body = {"code": "", "explanation": "", "error": "gave up", "error_type": "iteration_limit"}

    with patch.object(MeepService, "write_code", return_value=body):
        response = await mcp_client.call_tool("generate_code", {"problem_description": "a waveguide"})

    blob = _blob(response)
    assert "do NOT resend the same description" in blob.replace("Do NOT", "do NOT")
    assert response.is_error is False


@pytest.mark.asyncio
async def test_generate_code_generation_error_allows_one_retry(mcp_client):
    body = {"code": "", "explanation": "", "error": "backend blew up", "error_type": "generation_error"}

    with patch.object(MeepService, "write_code", return_value=body):
        response = await mcp_client.call_tool("generate_code", {"problem_description": "a waveguide"})

    assert "transient" in _blob(response)


@pytest.mark.asyncio
async def test_generate_code_forwards_retry_arguments(mcp_client):
    body = {"code": "import meep", "explanation": "fixed", "error": None}

    with patch.object(MeepService, "write_code", return_value=body) as mock_write:
        await mcp_client.call_tool(
            "generate_code",
            {"problem_description": "a bend", "previous_code": "old code", "previous_error": "Traceback ..."},
        )

    mock_write.assert_called_once_with("a bend", "old code", "Traceback ...")


@pytest.mark.asyncio
async def test_generate_code_transport_failure_raises(mcp_client):
    """Unlike a generation failure, a transport error must surface as a tool error."""
    with patch.object(MeepService, "write_code", side_effect=RuntimeError("connection refused")):
        response = await mcp_client.call_tool("generate_code", {"problem_description": "x"}, raise_on_error=False)

    assert response.is_error is True


# ── execute_code ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_code_queued(mcp_client):
    body = {"task_id": "job-1", "status": "queued", "exports_detected": ["ez", "max_ez"], "info": "Detected 2 export(s): ez, max_ez"}

    with patch.object(MeepService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "import meep as mp\nexport('ez', 1)"})

    blob = _blob(response)
    assert "job-1" in blob
    assert "ez, max_ez" in blob
    assert "get_simulation_status" in blob


@pytest.mark.asyncio
async def test_execute_code_no_exports_is_a_finding_not_an_error(mcp_client):
    """A rejected script is a legitimate result: it must come back as content, not raise."""
    body = {"success": False, "error": "no export() call found.", "error_type": "no_exports", "status_code": 400}

    with patch.object(MeepService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "print(1)"})

    assert response.is_error is False
    assert "export('name', obj)" in _blob(response)


@pytest.mark.asyncio
async def test_execute_code_transport_failure_raises(mcp_client):
    with patch.object(MeepService, "execute_code", side_effect=RuntimeError("connection refused")):
        response = await mcp_client.call_tool("execute_code", {"code": "import meep"}, raise_on_error=False)

    assert response.is_error is True


@pytest.mark.asyncio
async def test_execute_code_syntax_error_reports_line(mcp_client):
    body = {"success": False, "error": "unexpected EOF", "error_type": "syntax_error", "status_code": 400, "lineno": 12}

    with patch.object(MeepService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "import meep as mp\nx = ("})

    assert "line 12" in _blob(response)


@pytest.mark.asyncio
async def test_execute_code_missing_lineno_does_not_print_none(mcp_client):
    for body in (
        {"success": False, "error": "bad", "error_type": "syntax_error", "status_code": 400},
        {"success": False, "error": "bad", "error_type": "syntax_error", "status_code": 400, "lineno": None},
    ):
        with patch.object(MeepService, "execute_code", return_value=body):
            response = await mcp_client.call_tool("execute_code", {"code": "x = ("})
        blob = _blob(response)
        assert "None" not in blob
        assert "line" not in blob.split("not valid Python")[1].split(":")[0]


@pytest.mark.asyncio
async def test_execute_code_forbidden_explains_playground_role(mcp_client):
    body = {"success": False, "error": "Not authorized", "error_type": "http_error", "status_code": 403}

    with patch.object(MeepService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "import meep"})

    blob = _blob(response)
    assert response.is_error is False
    assert "PLAYGROUND" in blob
    assert "generate_code still works" in blob


@pytest.mark.asyncio
async def test_execute_code_scheduler_error_is_infrastructure(mcp_client):
    body = {"success": False, "error": "Unsupported dependency os", "error_type": "scheduler_error", "status_code": 502}

    with patch.object(MeepService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "import meep"})

    assert "infrastructure failure" in _blob(response)


# ── get_simulation_status ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_status_without_wait_polls_once(mcp_client):
    body = {"task_id": "job-1", "status": "running", "error_trace": None}

    with patch.object(MeepService, "get_status", return_value=body) as mock_status:
        response = await mcp_client.call_tool("get_simulation_status", {"task_id": "job-1"})

    mock_status.assert_called_once_with("job-1")
    assert "wait_seconds=120" in _blob(response)


@pytest.mark.asyncio
async def test_get_status_returns_early_when_already_terminal(mcp_client):
    body = {"task_id": "job-1", "status": "completed", "error_trace": None}

    with patch.object(MeepService, "get_status", return_value=body) as mock_status:
        response = await mcp_client.call_tool("get_simulation_status", {"task_id": "job-1", "wait_seconds": 120})

    mock_status.assert_called_once_with("job-1")
    assert "get_results" in _blob(response)


@pytest.mark.asyncio
async def test_get_status_polls_until_terminal(mcp_client, fast_poll):
    states = [
        {"task_id": "job-1", "status": "queued"},
        {"task_id": "job-1", "status": "running"},
        {"task_id": "job-1", "status": "completed"},
    ]

    with patch.object(MeepService, "get_status", side_effect=states) as mock_status:
        response = await mcp_client.call_tool("get_simulation_status", {"task_id": "job-1", "wait_seconds": 5})

    assert mock_status.call_count == 3
    assert "completed" in _blob(response)


@pytest.mark.asyncio
async def test_get_status_still_running_when_budget_expires(mcp_client, fast_poll):
    body = {"task_id": "job-1", "status": "running"}

    with patch.object(MeepService, "get_status", return_value=body) as mock_status:
        response = await mcp_client.call_tool("get_simulation_status", {"task_id": "job-1", "wait_seconds": 1})

    assert mock_status.call_count > 1
    assert "Chain at most" in _blob(response)


@pytest.mark.asyncio
async def test_get_status_failed_surfaces_trace_and_retry_advice(mcp_client):
    body = {"task_id": "job-1", "status": "failed", "error_trace": "RuntimeError: meep exploded"}

    with patch.object(MeepService, "get_status", return_value=body):
        response = await mcp_client.call_tool("get_simulation_status", {"task_id": "job-1"})

    blob = _blob(response)
    assert "meep exploded" in blob
    assert "previous_error" in blob


@pytest.mark.asyncio
async def test_get_status_failed_directs_result_retrieval_before_retry(mcp_client):
    body = {"task_id": "job-1", "status": "failed", "error_trace": "RuntimeError: fields are NaN"}

    with patch.object(MeepService, "get_status", return_value=body):
        response = await mcp_client.call_tool("get_simulation_status", {"task_id": "job-1"})

    blob = _blob(response)
    assert "get_results" in blob
    assert blob.index("get_results") < blob.index("generate_code")


@pytest.mark.asyncio
async def test_get_status_failed_without_trace_does_not_print_none(mcp_client):
    body = {"task_id": "job-1", "status": "failed", "error_trace": None}

    with patch.object(MeepService, "get_status", return_value=body):
        response = await mcp_client.call_tool("get_simulation_status", {"task_id": "job-1"})

    blob = _blob(response)
    assert "no error trace" in blob
    assert "None" not in blob


@pytest.mark.asyncio
async def test_get_status_task_not_found_returns_immediately(mcp_client, fast_poll):
    body = {"success": False, "error": "Job not found", "error_type": "task_not_found", "status_code": 404}

    with patch.object(MeepService, "get_status", return_value=body) as mock_status:
        response = await mcp_client.call_tool("get_simulation_status", {"task_id": "nope", "wait_seconds": 120})

    mock_status.assert_called_once_with("nope")
    assert "No meep job with that task_id" in _blob(response)


@pytest.mark.asyncio
async def test_get_status_forbidden_returns_immediately(mcp_client, fast_poll):
    body = {"success": False, "error": "Not authorized", "error_type": "http_error", "status_code": 403}

    with patch.object(MeepService, "get_status", return_value=body) as mock_status:
        response = await mcp_client.call_tool("get_simulation_status", {"task_id": "job-1", "wait_seconds": 120})

    mock_status.assert_called_once_with("job-1")
    assert "PLAYGROUND" in _blob(response)


@pytest.mark.asyncio
async def test_get_status_scheduler_error_is_retried_then_reported(mcp_client, fast_poll):
    body = {"success": False, "error": "scheduler unreachable", "error_type": "scheduler_error", "status_code": 502}

    with patch.object(MeepService, "get_status", return_value=body) as mock_status:
        response = await mcp_client.call_tool("get_simulation_status", {"task_id": "job-1", "wait_seconds": 1})

    assert mock_status.call_count > 1
    assert "infrastructure failure" in _blob(response)


# ── get_results ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_results_not_completed_points_at_status_tool(mcp_client):
    body = {"success": False, "error": "job not finished", "error_type": "not_completed", "status_code": 409, "status": "running"}

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1"})

    blob = _blob(response)
    assert response.is_error is False
    assert "get_simulation_status" in blob
    assert "running" in blob


@pytest.mark.asyncio
async def test_get_results_not_completed_for_failed_job_does_not_send_back_to_polling(mcp_client):
    """An older backend answers 409 for a failed job; polling for 'completed' would never end."""
    body = {"success": False, "error": "job failed", "error_type": "not_completed", "status_code": 409, "status": "failed"}

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1"})

    blob = _blob(response)
    assert "until it reports" not in blob
    assert "Do not poll" in blob
    assert "previous_error" in blob


@pytest.mark.asyncio
async def test_get_results_leads_with_failed_verification_finding(mcp_client, tmp_path):
    diagnosis = _finding()
    body = _results({}, execution_status="failed", diagnosis=diagnosis)

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    first_text = _texts(response)[0]
    assert first_text.startswith("Verification: NOT passed.")
    assert "courant_unstable" in first_text
    assert "courant=1.2" in first_text
    assert "limit=1.0" in first_text
    assert "Lower the Courant factor" in first_text


@pytest.mark.asyncio
async def test_get_results_reports_setup_findings(mcp_client, tmp_path):
    finding = _finding(
        "under_resolved_in_material",
        source="static",
        suggestion="Increase resolution.",
        detail={"pixels_per_wavelength": 3.2, "minimum": 10.0},
    )
    body = _results({}, setup_findings=[finding])

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    first_text = _texts(response)[0]
    assert first_text.startswith("Verification: NOT passed.")
    assert "pre-solve under_resolved_in_material" in first_text
    assert "Increase resolution" in first_text


@pytest.mark.asyncio
async def test_get_results_preserves_verification_fields_in_structured_content(mcp_client, tmp_path):
    diagnosis = _finding()
    setup_finding = _finding("structure_in_pml", source="static", suggestion="Move the structure out of the PML.")
    body = _results({}, execution_status="failed", diagnosis=diagnosis, setup_findings=[setup_finding])

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    assert response.structured_content["execution_status"] == "failed"
    assert response.structured_content["diagnosis"] == diagnosis
    assert response.structured_content["setup_findings"] == [setup_finding]


@pytest.mark.asyncio
async def test_get_results_writes_checks_json_beside_exports(mcp_client, tmp_path):
    diagnosis = _finding()
    body = _results({}, diagnosis=diagnosis)

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    checks_path = tmp_path / "meep_job-1" / "checks.json"
    assert json.loads(checks_path.read_text()) == {
        "task_id": "job-1",
        "execution_status": "completed",
        "diagnosis": diagnosis,
        "setup_findings": [],
    }
    assert response.structured_content["checks_path"] == str(checks_path)


@pytest.mark.asyncio
async def test_checks_json_does_not_overwrite_an_export_named_checks(mcp_client, tmp_path):
    exported_checks = '{"owner":"user export"}'
    body = _results(
        {"checks": {"kind": "text", "payload": exported_checks, "size_bytes": len(exported_checks)}},
        diagnosis=_finding(),
    )

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    checks_path = response.structured_content["checks_path"]
    export_path = response.structured_content["exports"]["checks"]["path"]
    assert export_path != checks_path
    assert json.loads((tmp_path / "meep_job-1" / "checks.json").read_text())["diagnosis"]["kind"] == "courant_unstable"
    assert (tmp_path / "meep_job-1" / "checks (1).json").read_text() == exported_checks


@pytest.mark.asyncio
async def test_get_results_clean_run_does_not_claim_accuracy(mcp_client, tmp_path):
    body = _results({})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    first_text = _texts(response)[0]
    assert first_text.startswith("Verification:")
    assert "no findings reported" in first_text
    assert "convergence and accuracy were not established" in first_text


@pytest.mark.asyncio
async def test_get_results_marks_which_findings_failed(mcp_client, tmp_path):
    diagnosis = {**_finding("healthy"), "passed": True, "diverged": False}
    setup_finding = _finding("structure_in_pml", source="static", suggestion="Move the structure out of the PML.")
    body = _results({}, diagnosis=diagnosis, setup_findings=[setup_finding])

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    first_text = _texts(response)[0]
    assert "1 verification finding(s) failed" in first_text
    assert "- passed: post-run healthy" in first_text
    assert "- FAILED: pre-solve structure_in_pml" in first_text


@pytest.mark.asyncio
async def test_get_results_surfaces_decay_divergence_and_engine_warnings(mcp_client, tmp_path):
    diagnosis = {
        **_finding("healthy"),
        "passed": True,
        "diverged": True,
        "final_decay_value": 0.02,
        "shutoff_target": 0.001,
        "engine_warnings": ["PML thinner than half a wavelength"],
    }
    body = _results({}, diagnosis=diagnosis)

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    first_text = _texts(response)[0]
    assert "engine raised 1 warning(s)" in first_text
    assert "reported no failures." not in first_text
    assert "fields diverged" in first_text
    assert "final decay 0.02 vs shutoff target 0.001" in first_text
    assert "engine warning: PML thinner than half a wavelength" in first_text


@pytest.mark.asyncio
async def test_get_results_summarizes_array_and_writes_file(mcp_client, tmp_path):
    payload = _npy_b64(np.array([1.0, 2.0, 3.0, np.nan]))
    body = _results({"ez": {"kind": "npy", "payload": payload, "size_bytes": 0}})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    blob = _blob(response)
    assert "shape=(4,)" in blob
    assert "dtype=float64" in blob
    assert "non-finite=1" in blob
    # The raw payload must never reach the caller's context.
    assert payload[:32] not in blob
    written = list(tmp_path.rglob("ez.npy"))
    assert len(written) == 1
    assert np.load(written[0], allow_pickle=False).shape == (4,)
    assert response.structured_content["exports"]["ez"]["path"] == str(written[0])


@pytest.mark.asyncio
async def test_get_results_returns_png_as_image_content(mcp_client, tmp_path):
    body = _results({"field_fig": {"kind": "png", "payload": PNG_B64, "size_bytes": len(PNG_BYTES)}})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    images = [block for block in response.content if getattr(block, "mime_type", None) == "image/png"]
    assert len(images) == 1
    assert list(tmp_path.rglob("field_fig.png"))


@pytest.mark.asyncio
async def test_get_results_pickle_is_never_decoded(mcp_client, tmp_path):
    body = _results({"obj": {"kind": "pickle", "payload": base64.b64encode(b"\x80 not really a pickle").decode(), "size_bytes": 20}})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    blob = _blob(response)
    assert response.is_error is False
    assert "dill" in blob
    assert list(tmp_path.rglob("obj.pkl"))


@pytest.mark.asyncio
async def test_get_results_scalar_export_prints_exact_value(mcp_client, tmp_path):
    body = _results({"max_ez": {"kind": "npy", "payload": _npy_b64(np.float64(0.299)), "size_bytes": 0}})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    blob = _blob(response)
    assert "value=0.299" in blob
    assert "0.000" not in blob


@pytest.mark.asyncio
async def test_get_results_string_array_does_not_crash(mcp_client, tmp_path):
    body = _results({"labels": {"kind": "npy", "payload": _npy_b64(np.array(["ab", "cd"])), "size_bytes": 0}})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    assert response.is_error is False
    assert "shape=(2,)" in _blob(response)


@pytest.mark.asyncio
async def test_get_results_npz_lists_members(mcp_client, tmp_path):
    payload = _npz_b64(flux=np.array([1.0, 2.0]), wavelength=np.array([1.5, 1.6]))
    body = _results({"spectrum": {"kind": "npz", "payload": payload, "size_bytes": 0}})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    blob = _blob(response)
    assert "flux" in blob
    assert "wavelength" in blob
    assert list(tmp_path.rglob("spectrum.npz"))


@pytest.mark.asyncio
async def test_get_results_json_text_export_written_as_json(mcp_client, tmp_path):
    body = _results({"meta": {"kind": "text", "payload": '{"resolution": 20}', "size_bytes": 18}})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    assert list(tmp_path.rglob("meta.json"))
    assert "resolution" in _blob(response)


@pytest.mark.asyncio
async def test_get_results_invalid_base64_becomes_failed_object(mcp_client, tmp_path):
    body = _results(
        {
            "broken": {"kind": "npy", "payload": "!!!not base64!!!", "size_bytes": 0},
            "ok": {"kind": "npy", "payload": _npy_b64(np.arange(3)), "size_bytes": 0},
        }
    )

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    blob = _blob(response)
    assert response.is_error is False
    assert "not valid base64" in blob
    assert "shape=(3,)" in blob
    assert "broken" in response.structured_content["failed_objects"]


@pytest.mark.asyncio
async def test_get_results_sanitizes_export_names(mcp_client, tmp_path):
    body = _results({"../../evil": {"kind": "npy", "payload": _npy_b64(np.arange(2)), "size_bytes": 0}})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "../../etc", "output_dir": str(tmp_path)})

    written = [p.resolve() for p in tmp_path.rglob("*") if p.is_file()]
    assert written
    assert all(path.is_relative_to(tmp_path.resolve()) for path in written)
    assert response.is_error is False


@pytest.mark.asyncio
async def test_get_results_truncates_long_console_and_keeps_full_log(mcp_client, tmp_path):
    body = _results({}, console_output="x" * 20000)

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    blob = _blob(response)
    assert "console truncated" in blob
    log = list(tmp_path.rglob("console.txt"))
    assert len(log) == 1
    assert len(log[0].read_text()) == 20000


@pytest.mark.asyncio
async def test_get_results_empty_console_is_reported(mcp_client, tmp_path):
    body = _results({"ez": {"kind": "npy", "payload": _npy_b64(np.arange(2)), "size_bytes": 0}}, console_output="")

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    assert "no console output" in _blob(response)


@pytest.mark.asyncio
async def test_get_results_no_exports_explains_itself(mcp_client, tmp_path):
    body = _results({})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    assert "produced no exports" in _blob(response)


@pytest.mark.asyncio
async def test_get_results_failed_job_without_exports_does_not_claim_completion(mcp_client, tmp_path):
    body = _results({}, execution_status="failed", diagnosis=_finding())

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    blob = _blob(response)
    assert "The job failed and produced no exports" in blob
    assert "completed but produced no exports" not in blob
    assert "never ran" not in blob


@pytest.mark.asyncio
async def test_get_results_honours_output_dir_env_var(mcp_client, tmp_path, monkeypatch):
    monkeypatch.setenv("AXIOMATIC_MEEP_OUTPUT_DIR", str(tmp_path))
    body = _results({"ez": {"kind": "npy", "payload": _npy_b64(np.arange(2)), "size_bytes": 0}})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1"})

    assert response.structured_content["output_dir"] == str((tmp_path / "meep_job-1").resolve())
    assert list(tmp_path.rglob("ez.npy"))


@pytest.mark.asyncio
async def test_get_results_zero_size_and_empty_text_are_not_treated_as_absent(mcp_client, tmp_path):
    """size_bytes: 0 and an empty text payload are legitimate values, not missing fields."""
    body = _results({"empty_note": {"kind": "text", "payload": "", "size_bytes": 0}})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    blob = _blob(response)
    assert "empty text export" in blob
    assert response.structured_content["exports"]["empty_note"]["size_bytes"] == 0


@pytest.mark.asyncio
async def test_get_results_survives_unwritable_output_dir(mcp_client, tmp_path):
    """A disk problem must not lose a completed simulation's results."""
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory")
    body = _results({"ez": {"kind": "npy", "payload": _npy_b64(np.arange(2)), "size_bytes": 0}})

    with patch.object(MeepService, "get_results", return_value=body):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(blocked)})

    blob = _blob(response)
    assert response.is_error is False
    assert "could NOT be written" in blob
    assert "ez" in blob
    assert response.structured_content["checks_path"] is None


@pytest.mark.asyncio
async def test_get_results_reports_checks_path_written_before_a_later_disk_failure(mcp_client, tmp_path):
    body = _results({"ez": {"kind": "npy", "payload": _npy_b64(np.arange(2)), "size_bytes": 0}}, diagnosis=_finding())

    with (
        patch.object(MeepService, "get_results", return_value=body),
        patch("axiomatic_mcp.servers.meep.server.summarize_exports", side_effect=OSError("disk full")),
    ):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1", "output_dir": str(tmp_path)})

    checks_path = tmp_path / "meep_job-1" / "checks.json"
    assert checks_path.exists()
    assert response.structured_content["checks_path"] == str(checks_path)
    assert response.structured_content["output_dir"] == str(tmp_path / "meep_job-1")
    assert str(checks_path) in _blob(response)


@pytest.mark.asyncio
async def test_get_results_transport_failure_raises(mcp_client):
    with patch.object(MeepService, "get_results", side_effect=RuntimeError("connection refused")):
        response = await mcp_client.call_tool("get_results", {"task_id": "job-1"}, raise_on_error=False)

    assert response.is_error is True
