"""Tests for the AxArgmin MCP server.

Focused on the `verification` payload: `success` reports only that the generated code ran,
so whether the *answers* are solved reaches the caller through this field and nowhere else.
A payload that arrived but went unmentioned in the tool's text would be a silent regression
-- the model reads the content blocks, not the structured result -- so the wording is
asserted here alongside the pass-through.
"""

from unittest.mock import patch

import pytest
import pytest_asyncio
from fastmcp.client import Client

from axiomatic_mcp.servers.argmin.server import _verification_text, mcp
from axiomatic_mcp.servers.argmin.services.argmin_service import ArgminService
from axiomatic_mcp.shared.constants.api_constants import ApiRoutes

SERVICE_CLIENT = "axiomatic_mcp.servers.argmin.services.argmin_service.AxiomaticAPIClient"


def _certificate(passed: bool) -> dict:
    return {
        "kkt_stationarity_inf": 3.5e-10 if passed else 3.0,
        "constraint_violation_upper": 0.0,
        "tolerances": {"tol": 1e-08},
        "passed": passed,
        "primal_finite": True,
    }


def _verified_response() -> dict:
    return {
        "success": True,
        "result": {"result": {"success": True, "status": "Solve_Succeeded", "objective_value": 0.5}},
        "error": None,
        "stdout": None,
        "execution_time": 0.42,
        "verification": {
            "_summary": {"all_passed": True, "n_verifiable": 1, "n_passed": 1, "n_failed": 0, "n_unknown": 0},
            "_warnings": [],
            "result": {
                "passed": True,
                "solver_success": True,
                "solver_status": "Solve_Succeeded",
                "certificate": _certificate(True),
                "diagnosis": None,
            },
        },
    }


def _unverified_response() -> dict:
    return {
        "success": True,
        "result": {"result": {"success": False, "status": "Infeasible_Problem_Detected", "objective_value": None}},
        "error": None,
        "stdout": None,
        "execution_time": 0.18,
        "verification": {
            "_summary": {"all_passed": False, "n_verifiable": 1, "n_passed": 0, "n_failed": 1, "n_unknown": 0},
            "_warnings": ["result: KKT stationarity 3 exceeds tol 1e-08"],
            "result": {
                "passed": False,
                "solver_success": False,
                "solver_status": "Infeasible_Problem_Detected",
                "certificate": _certificate(False),
                "diagnosis": {
                    "kind": "infeasible_detected",
                    "solver_return_status": "Infeasible_Problem_Detected",
                    "message": "Infeasible problem detected",
                    "suggestion": "Check constraints for contradictions or relax bounds.",
                },
            },
        },
    }


def _mock_client(mock_client_cls, response):
    client = mock_client_cls.return_value.__enter__.return_value
    client.post.return_value = response
    return client


def _texts(response) -> list[str]:
    return [block.text for block in response.content if hasattr(block, "text")]


def _blob(response) -> str:
    return "\n".join(_texts(response))


@pytest_asyncio.fixture
async def mcp_client():
    async with Client(transport=mcp) as client:
        yield client


# ── routes and registration ──────────────────────────────────────────────────


def test_routes_point_at_argmin_endpoints():
    assert ApiRoutes.ARGMIN_WRITE_CODE == "/numerics/argmin/write-code"
    assert ApiRoutes.ARGMIN_EXECUTE == "/numerics/argmin/execute"


@pytest.mark.asyncio
async def test_list_tools(mcp_client):
    tool_names = {t.name for t in await mcp_client.list_tools()}
    assert {"generate_code", "execute_code"} <= tool_names


@pytest.mark.asyncio
async def test_execute_declares_no_output_schema(mcp_client):
    """The absence is the guarantee — see the comment above `_NOTHING_EXPORTED_TEXT`.

    fastmcp derives the client's `.data` from a declared schema and keeps only what the
    schema names, so any schema here silently deletes the per-export certificates. Asserted
    rather than left to a comment because adding one back looks like an improvement.
    """
    tools = {t.name: t for t in await mcp_client.list_tools()}
    assert tools["execute_code"].outputSchema is None


@pytest.mark.asyncio
async def test_the_certificate_survives_all_the_way_into_client_data(mcp_client):
    """`.data` is what a fastmcp client reads; the evidence has to be there, not just in the raw dict."""
    body = _verified_response()

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    assert response.data == body
    assert response.data["verification"]["result"]["certificate"]["kkt_stationarity_inf"] == 3.5e-10
    assert response.data["result"]["result"]["objective_value"] == 0.5


def test_instructions_tell_the_client_where_the_verdict_lives():
    assert "all_passed" in mcp.instructions
    assert "says only that the code RAN" in mcp.instructions


def test_instructions_describe_the_verdict_the_code_actually_produces():
    """The model-facing contract has to match `_verification_text`, not trail it.

    These two claims drifted behind the code twice: the precedence rule listed only one of
    the reasons a pass is refused, and the `_warnings` line still called every warning a
    finding after the advisory case was established. Both are asserted against the behaviour
    rather than the wording alone, so the next change to one has to update the other.
    """
    instructions = mcp.instructions
    advisory = ["export '_summary' collides with a reserved verification key"]

    # Claim: a pass is refused when nothing was counted, AND when a count contradicts the flag.
    assert "n_failed" in instructions and "n_unknown" in instructions
    assert _verification_text({"_summary": {"all_passed": True, "n_verifiable": 0}}).startswith("Verification: inconclusive")
    assert _verification_text({"_summary": {"all_passed": True, "n_verifiable": 3, "n_failed": 1}}).startswith("Verification: NOT passed")

    # Claim: a warning is not by itself a failure, and the verdict line says whether it mattered.
    assert "not by itself a failure" in instructions
    clean_with_advisory = _verification_text(
        {"_summary": {"all_passed": True, "n_verifiable": 1, "n_failed": 0, "n_unknown": 0}, "_warnings": advisory}
    )
    assert clean_with_advisory.startswith("Verification: passed")
    assert advisory[0] in clean_with_advisory


# ── service layer ────────────────────────────────────────────────────────────


def test_generate_code_sends_json_body():
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, {"code": "c", "explanation": "e", "error": None})
        ArgminService().generate_code("minimize x^2", "nonlinear_program")

    client.post.assert_called_once_with(
        "/numerics/argmin/write-code",
        data={"problem_description": "minimize x^2", "problem_type": "nonlinear_program"},
    )


def test_execute_code_sends_json_body():
    with patch(SERVICE_CLIENT) as mock_client_cls:
        client = _mock_client(mock_client_cls, _verified_response())
        ArgminService().execute_code("export('x', 1)")

    client.post.assert_called_once_with("/numerics/argmin/execute", data={"code": "export('x', 1)"})


# ── generate_code ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_code_rejects_an_unknown_problem_type(mcp_client):
    with pytest.raises(Exception, match="Invalid problem_type"):
        await mcp_client.call_tool("generate_code", {"problem_description": "x^2", "problem_type": "quantum"})


@pytest.mark.asyncio
async def test_generate_code_returns_the_code_block(mcp_client):
    body = {"code": "export('x', 1)", "explanation": "square it", "error": None}

    with patch.object(ArgminService, "generate_code", return_value=body):
        response = await mcp_client.call_tool("generate_code", {"problem_description": "minimize x^2", "problem_type": "nonlinear_program"})

    assert "square it" in _blob(response)
    assert "```python\nexport('x', 1)\n```" in _blob(response)


# ── execute_code: the verification payload ───────────────────────────────────


@pytest.mark.asyncio
async def test_verified_solve_says_so_and_passes_the_payload_through(mcp_client):
    body = _verified_response()

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    assert "Verification: passed" in _texts(response)[0]
    assert response.structured_content == body


@pytest.mark.asyncio
async def test_a_failed_solve_is_reported_without_being_turned_into_an_error(mcp_client):
    """Report, don't block: the code ran, so the exports and the diagnosis must survive."""
    body = _unverified_response()

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    assert not response.is_error
    verdict = _texts(response)[0]
    assert "Verification: NOT passed" in verdict
    assert "KKT stationarity 3 exceeds tol 1e-08" in verdict
    assert "Do not report these numbers as the answer" in verdict
    assert response.structured_content["verification"]["result"]["diagnosis"]["kind"] == "infeasible_detected"


@pytest.mark.asyncio
async def test_the_verdict_is_read_before_the_numbers(mcp_client):
    """A diverged solve returns success=true; in the other order the exports read as an answer."""
    with patch.object(ArgminService, "execute_code", return_value=_unverified_response()):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    texts = _texts(response)
    assert texts[0].startswith("Verification:")
    assert any(text.startswith("Result:") for text in texts[1:])


@pytest.mark.asyncio
async def test_nothing_verifiable_is_named_as_such_not_reported_as_a_pass(mcp_client):
    """`verification: null` must never read as "checked and fine"."""
    body = {"success": True, "result": {"x": 2.0}, "error": None, "stdout": None, "execution_time": 0.01, "verification": None}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('x', 2.0)"})

    verdict = _texts(response)[0]
    assert "Verification: none" in verdict
    assert "passed" not in verdict.lower().split("export(")[0]
    assert "export('result', result)" in verdict


@pytest.mark.asyncio
async def test_an_older_backend_is_not_blamed_on_the_generated_code(mcp_client):
    """The key is simply absent against a backend that predates the payload.

    Reported live against the deployed API today, so this is the common path, not a corner
    case. The exports hold a solver result, which a current executor would always have
    reported on -- so telling the agent to "export the result" would send it rewriting code
    that was already correct.
    """
    body = {
        "success": True,
        "result": {"result": {"success": True, "status": "Solve_Succeeded", "objective_value": 0.5}},
        "error": None,
        "stdout": None,
        "execution_time": 0.01,
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: unavailable" in verdict
    assert "do not rewrite it" in verdict
    assert "export('result', result)" not in verdict


@pytest.mark.asyncio
async def test_a_missing_payload_with_no_solver_result_still_blames_the_code(mcp_client):
    """The other side of the same discrimination: nothing was exported to check."""
    body = {"success": True, "result": {"x": 2.0}, "error": None, "stdout": None, "execution_time": 0.01}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('x', 2.0)"})

    assert "Verification: none" in _texts(response)[0]


@pytest.mark.asyncio
async def test_a_stated_failure_without_counts_is_still_a_failure(mcp_client):
    """The payload is an open object; a shape this server does not know must not crash it.

    `all_passed: false` says the answer is not solved, so the counts being absent must not
    soften that into "inconclusive" — the reader still needs to be told not to use it.
    """
    body = {
        "success": True,
        "result": {"result": {}},
        "execution_time": 0.1,
        "verification": {"_summary": {"all_passed": False}, "_warnings": []},
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: NOT passed" in verdict
    assert "Do not report these numbers as the answer" in verdict


@pytest.mark.asyncio
async def test_findings_survive_a_payload_with_no_summary_at_all(mcp_client):
    """The warnings ARE the finding; an inconclusive verdict would throw them away.

    A payload carrying per-export entries and `_warnings` but no `_summary` is the most
    plausible unknown shape, and it is exactly the one where the detail matters most.
    """
    body = {
        "success": True,
        "result": {"result": {}},
        "execution_time": 0.1,
        "verification": {
            "_warnings": ["result: KKT stationarity 3 exceeds tol 1e-08"],
            "result": {"passed": False, "diagnosis": {"kind": "diverged"}},
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: NOT passed" in verdict
    assert "KKT stationarity 3 exceeds tol 1e-08" in verdict
    assert "Do not report these numbers as the answer" in verdict


@pytest.mark.asyncio
async def test_failure_counts_without_a_total_are_reported_coherently(mcp_client):
    """No `n_verifiable`, so the sentence must not read "of 0 checked solve(s) 2 failed"."""
    body = {
        "success": True,
        "result": {"result": {}},
        "execution_time": 0.1,
        "verification": {"_summary": {"all_passed": False, "n_failed": 2}, "_warnings": []},
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: NOT passed" in verdict
    assert "2 solve(s) failed their certificate" in verdict
    assert "of 0 checked" not in verdict


@pytest.mark.asyncio
@pytest.mark.parametrize("counts", [{"n_failed": 1}, {"n_unknown": 1}])
async def test_a_pass_flag_beside_a_failure_count_is_not_a_pass(mcp_client, counts):
    """`all_passed` is defined backend-side as n_failed == 0 and n_unknown == 0.

    A true flag beside a positive count is a contradiction, and the safe reading of a
    contradiction about whether an answer is solved is that it is not. Without this the
    warning line, the certificate and the diagnosis are all dropped and the answer goes
    out certified.
    """
    body = {
        "success": True,
        "result": {"result": {}},
        "execution_time": 0.1,
        "verification": {
            "_summary": {"all_passed": True, "n_verifiable": 3, "n_passed": 2, **counts},
            "_warnings": ["result_b: KKT stationarity 3.0 exceeds tol 1e-08"],
            "result_b": {"passed": False, "diagnosis": {"kind": "infeasible_detected"}},
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: NOT passed" in verdict
    assert "Verification: passed" not in verdict
    assert "KKT stationarity 3.0 exceeds tol 1e-08" in verdict
    assert "Do not report these numbers as the answer" in verdict


@pytest.mark.asyncio
async def test_an_advisory_warning_does_not_downgrade_a_clean_run(mcp_client):
    """Not every warning is a finding, so a warning alone must not fail a passing solve.

    `_warnings_for` returns nothing for a passing entry, but the backend also emits a
    reserved-key collision warning whether or not the colliding export passed -- an
    advisory beside a clean run is a real shape. It is carried into the pass text rather
    than swallowed, so the reader still sees it.
    """
    body = {
        "success": True,
        "result": {"result": {}},
        "execution_time": 0.1,
        "verification": {
            "_summary": {"all_passed": True, "n_verifiable": 1, "n_passed": 1, "n_failed": 0, "n_unknown": 0},
            "_warnings": ["export '_summary' collides with a reserved verification key"],
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: passed" in verdict
    assert "collides with a reserved verification key" in verdict


@pytest.mark.asyncio
async def test_a_warning_driven_verdict_does_not_contradict_its_own_counts(mcp_client):
    """No failure is counted, so the sentence must not read "0 failed ... 0 produced none"."""
    body = {
        "success": True,
        "result": {"result": {}},
        "execution_time": 0.1,
        "verification": {"_summary": {"n_verifiable": 3}, "_warnings": ["result_b: diverged"]},
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: NOT passed" in verdict
    assert "none of the 3 checked solve(s) is counted as failed" in verdict
    assert "0 failed their certificate" not in verdict


@pytest.mark.asyncio
async def test_a_non_dict_payload_on_a_failed_run_is_not_called_a_stale_backend(mcp_client):
    """The two gates must agree on what counts as a payload, or they contradict each other."""
    body = {"success": False, "result": None, "error": "boom", "verification": "not a dict"}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export("})

    blob = _blob(response)
    assert "Execution failed: boom" in blob
    assert "predates the certificate payload" not in blob


@pytest.mark.asyncio
async def test_an_empty_payload_naming_nothing_is_inconclusive(mcp_client):
    """Nothing counted and nothing reported: the one case that really is inconclusive."""
    body = {"success": True, "result": {"result": {}}, "execution_time": 0.1, "verification": {"_summary": {}, "_warnings": []}}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    assert "Verification: inconclusive" in _texts(response)[0]


@pytest.mark.asyncio
async def test_a_count_json_spelled_as_a_float_still_counts(mcp_client):
    """`2` and `2.0` are the same number in JSON; rejecting the float downgrades a real pass."""
    body = {
        "success": True,
        "result": {"result": {}},
        "execution_time": 0.1,
        "verification": {"_summary": {"all_passed": True, "n_verifiable": 2.0}, "_warnings": []},
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    assert "Verification: passed. All 2 exported solve(s)" in _texts(response)[0]


@pytest.mark.asyncio
async def test_a_pass_over_nothing_is_not_reported_as_a_pass(mcp_client):
    """`all_passed` true with no counted solve certifies nothing, whatever the flag says.

    The whole feature exists to stop an unchecked answer being reported as certified, so
    the one claim a caller acts on is not made on the strength of a single flag in a
    payload built to keep growing.
    """
    body = {
        "success": True,
        "result": {"result": {}},
        "execution_time": 0.1,
        "verification": {"_summary": {"all_passed": True, "n_verifiable": 0}, "_warnings": []},
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: inconclusive" in verdict
    assert "Verification: passed" not in verdict


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "verification",
    ["a string", 42, ["a", "list"], {"_summary": "not a dict"}, {"_summary": {"all_passed": True, "n_verifiable": None}}],
)
async def test_an_unknown_payload_shape_never_raises(mcp_client, verification):
    """Documented as open and unknown-tolerant, so it has to actually tolerate the unknown."""
    body = {"success": True, "result": {"x": 1.0}, "execution_time": 0.1, "verification": verification}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('x', 1.0)"})

    assert not response.is_error
    assert _texts(response)[0].startswith("Verification:")


@pytest.mark.asyncio
async def test_a_null_execution_time_does_not_break_the_response(mcp_client):
    """The backend types this field nullable; formatting None with :.3f raises TypeError."""
    body = {"success": True, "result": {"x": 1.0}, "execution_time": None, "verification": None}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('x', 1.0)"})

    assert not response.is_error
    assert not any("Execution time" in text for text in _texts(response))


@pytest.mark.asyncio
async def test_a_nested_solver_result_counts_as_exported(mcp_client):
    """A multistart exports a list of results; that is a result reaching the caller too.

    Checking only top-level exports would tell the agent it exported nothing verifiable --
    the exact wrong instruction this discrimination exists to avoid.
    """
    body = {
        "success": True,
        "result": {"runs": [{"success": True, "status": "Solve_Succeeded"}, {"success": False, "status": "Infeasible"}]},
        "execution_time": 0.1,
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('runs', runs)"})

    assert "Verification: unavailable" in _texts(response)[0]


@pytest.mark.asyncio
async def test_scalar_success_and_status_exports_are_not_mistaken_for_a_result(mcp_client):
    """The optimal-control examples export `success` and `status` as separate scalars.

    The exports mapping would then carry both marker keys itself, and treating it as a
    result would claim a stale backend on code that really did export nothing verifiable.
    """
    body = {
        "success": True,
        "result": {"success": True, "status": "Solve_Succeeded", "optimal_time": 1.2},
        "execution_time": 0.1,
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('success', result.success)"})

    assert "Verification: none" in _texts(response)[0]


# ── execute_code: the code itself failing ────────────────────────────────────


@pytest.mark.asyncio
async def test_code_that_did_not_run_reports_the_error(mcp_client):
    body = {"success": False, "result": None, "error": "SyntaxError: invalid syntax", "stdout": "partial\n"}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export("})

    blob = _blob(response)
    assert "Execution failed: SyntaxError: invalid syntax" in blob
    assert "partial" in blob
    # No verdict line: nothing ran, so there is nothing to have verified.
    assert "Verification:" not in blob
    assert response.structured_content == body
