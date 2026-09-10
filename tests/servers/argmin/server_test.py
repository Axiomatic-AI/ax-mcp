"""Tests for the AxArgmin MCP server.

Focused on the `verification` payload: `success` reports only that the generated code ran,
so whether the *answers* are solved reaches the caller through this field and nowhere else.
A payload that arrived but went unmentioned in the tool's text would be a silent regression
-- the model reads the content blocks, not the structured result -- so the wording is
asserted here alongside the pass-through.
"""

import json
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastmcp.client import Client

from axiomatic_mcp.servers.argmin.server import _verification_text, mcp
from axiomatic_mcp.servers.argmin.services.argmin_service import ArgminService
from axiomatic_mcp.shared.constants.api_constants import ApiRoutes

SERVICE_CLIENT = "axiomatic_mcp.servers.argmin.services.argmin_service.AxiomaticAPIClient"


def _certificate(passed: bool) -> dict:
    """Shaped after a real staging payload, tolerances map included.

    The backend sends a per-criterion `tolerances` map, not the single `tol` this fixture
    used to carry; a certificate here that is simpler than the real one stops being
    evidence that the real one is handled.
    """
    return {
        "kkt_stationarity_inf": 3.5e-10 if passed else 3.0,
        "constraint_violation_lower": 0.0,
        "constraint_violation_upper": 0.0,
        "bound_violation": 0.0,
        "complementarity_inf": 2.5e-09,
        "tolerances": {
            "tol": 1e-08,
            "constr_viol_tol": 1e-08,
            "bound_relaxation": 1e-08,
            "variable_bound_relaxation": 1e-08,
            "complementarity_target": 0.0,
            "stationarity": 1e-08,
            "complementarity": 1e-08,
        },
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


def _json_payload(response) -> dict:
    """The response recovered from the content blocks alone, the way a client that ignores
    `structuredContent` has to recover it. Exactly one block parses as a JSON object."""
    decoded = []
    for text in _texts(response):
        try:
            value = json.loads(text)
        except ValueError:
            continue
        if isinstance(value, dict):
            decoded.append(value)
    assert len(decoded) == 1, f"expected exactly one JSON object block, got {len(decoded)}"
    return decoded[0]


async def _execute_tool(mcp_client):
    return {t.name: t for t in await mcp_client.list_tools()}["execute_code"]


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
    """The absence is the guarantee — see the comment above `_NO_PAYLOAD_TEXT`.

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


def test_instructions_lead_with_the_verdict_line_and_stay_short():
    """The instructions ship on every turn, so they carry the verdict and nothing else.

    `all_passed` used to be named here as "the flag to read" one bullet before another bullet
    said the `Verification:` line overrides it — a contradiction in the block a model sees
    most often. The payload's shape belongs on the tool, which is asserted separately below.
    """
    instructions = mcp.instructions
    assert "says only that the code RAN" in instructions
    assert "`Verification:` line" in instructions
    assert "treat it as the verdict" in instructions
    # The detail moved to the tool description; it must not creep back in here.
    assert "all_passed" not in instructions
    assert "n_failed" not in instructions
    assert "KKT" not in instructions
    assert "reserved key" not in instructions


@pytest.mark.asyncio
async def test_the_tool_description_describes_the_verdict_the_code_actually_produces(mcp_client):
    """The model-facing contract has to match `_verification_text`, not trail it.

    These two claims drifted behind the code twice: the precedence rule listed only one of
    the reasons a pass is refused, and the `_warnings` line still called every warning a
    finding after the advisory case was established. Both are asserted against the behaviour
    rather than the wording alone, so the next change to one has to update the other.
    """
    description = (await _execute_tool(mcp_client)).description
    advisory = ["export '_summary' collides with a reserved verification key"]

    # Claim: a pass is refused when nothing was counted, AND when a count contradicts the flag.
    assert "n_failed" in description and "n_unknown" in description
    assert _verification_text({"_summary": {"all_passed": True, "n_verifiable": 0}}).startswith("Verification: inconclusive")
    assert _verification_text({"_summary": {"all_passed": True, "n_verifiable": 3, "n_failed": 1}}).startswith("Verification: NOT passed")

    # Claim: `all_passed` feeds the line rather than standing in for it.
    assert "not a substitute for it" in description

    # Claim: a warning is not by itself a failure, and the verdict line says whether it mattered.
    assert "not by itself a failure" in description
    clean_with_advisory = _verification_text(
        {
            "_summary": {"all_passed": True, "n_verifiable": 1, "n_passed": 1, "n_failed": 0, "n_unknown": 0},
            "_warnings": advisory,
            "result": {"passed": True, "solver_success": True, "certificate": _certificate(True), "diagnosis": None},
        }
    )
    assert clean_with_advisory.startswith("Verification: passed")
    assert advisory[0] in clean_with_advisory

    # Claim: a certificate with no solver verdict behind it is not reported as convergence.
    assert "certificate is not a solver verdict" in description
    certificate_only = _verification_text(
        {
            "_summary": {"all_passed": True, "n_verifiable": 1, "n_passed": 1, "n_failed": 0, "n_unknown": 0},
            "_warnings": [],
            "best_certificate": {"passed": True, "certificate": _certificate(True), "diagnosis": None},
        }
    )
    assert certificate_only.startswith("Verification: certificate only")


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
    assert json.loads(texts[1])["result"]["result"]["status"] == "Infeasible_Problem_Detected"


# ── execute_code: the JSON text block ────────────────────────────────────────


@pytest.mark.asyncio
async def test_the_payload_is_recoverable_from_the_text_blocks_alone(mcp_client):
    """MCP asks for the serialized structured content beside it, because clients ignore `.data`.

    A client that shows a model only the content blocks previously got the exports as a
    Python repr (`{'success': False, ...}` — unparseable) and no `verification` at all, which
    is the one field that reaches the caller nowhere else.
    """
    body = _unverified_response()

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    recovered = _json_payload(response)
    assert recovered == body
    assert recovered == response.structured_content
    # The evidence a text-only client used to lose entirely.
    assert recovered["verification"]["result"]["certificate"]["kkt_stationarity_inf"] == 3.0
    assert recovered["verification"]["result"]["diagnosis"]["suggestion"].startswith("Check constraints")


@pytest.mark.asyncio
async def test_the_json_block_is_json_not_a_python_repr(mcp_client):
    """The regression this replaces: `str(dict)` gives `None`/`True` and single quotes."""
    body = {"success": True, "result": {"x": None, "ok": True}, "verification": None, "execution_time": 0.1}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('x', None)"})

    dumped = _texts(response)[1]
    assert '"x": null' in dumped and '"ok": true' in dumped
    assert "'x'" not in dumped


@pytest.mark.asyncio
async def test_the_json_block_survives_a_value_that_will_not_serialize(mcp_client):
    """`default=str` is there so a bad value costs this block, not the verdict and the exports."""
    body = {"success": True, "result": {"x": {1, 2}}, "verification": None, "execution_time": 0.1}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('x', x)"}, raise_on_error=False)

    assert not response.is_error
    assert _texts(response)[0].startswith("Verification:")
    assert _json_payload(response)["success"] is True


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
@pytest.mark.parametrize(
    "exports",
    [
        # A solver result reaching the caller: what the sniffing read as proof of an old
        # deployment, and told the agent its code was fine.
        {"result": {"success": True, "status": "Solve_Succeeded", "objective_value": 0.5}},
        # A plain mapping that merely carries both marker keys. A *current* backend
        # legitimately returns no payload for this — there is no certificate in it — so
        # calling it a stale deployment is the same false cause in the other direction.
        {"summary": {"success": True, "status": "complete"}},
        # Nothing verifiable at all.
        {"x": 2.0},
    ],
)
async def test_a_missing_payload_names_both_causes_and_attributes_neither(mcp_client, exports):
    """No payload has two causes, and nothing in the response separates them.

    The exports used to be sniffed for something result-shaped to pick between "you did not
    export a result" and "this executor predates the payload". Both readings are wrong on
    real shapes — a mapping with `success`/`status` and no certificate in it is exactly what
    a current backend returns no payload for, and the executor also degrades to no payload
    when collecting one fails — and each carries an instruction, so naming the wrong cause
    costs more than naming none. Backend age needs an explicit capability signal, which the
    response does not carry.
    """
    body = {"success": True, "result": exports, "error": None, "stdout": None, "execution_time": 0.01}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: none" in verdict
    # Both causes named, neither asserted, and the one action that helps either way.
    assert "cannot tell them apart" in verdict
    assert "predates" in verdict
    assert "export('result', result)" in verdict
    assert "do not rewrite" not in verdict


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
    assert "2 did not verify (out of an unreported total)" in verdict
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
            "result": {"passed": True, "solver_success": True, "solver_status": "Solve_Succeeded", "certificate": _certificate(True)},
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: passed" in verdict
    assert "collides with a reserved verification key" in verdict


@pytest.mark.asyncio
async def test_a_warning_driven_verdict_does_not_contradict_its_own_counts(mcp_client):
    """No failure is counted, so the sentence must not read "0 did not verify"."""
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
    assert "0 did not verify" not in verdict


@pytest.mark.asyncio
async def test_a_non_dict_payload_on_a_failed_run_yields_no_verdict_line(mcp_client):
    """The two gates must agree on what counts as a payload, or they contradict each other."""
    body = {"success": False, "result": None, "error": "boom", "verification": "not a dict"}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export("}, raise_on_error=False)

    blob = _blob(response)
    assert "Execution failed: boom" in blob
    assert "Verification:" not in blob


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
        "verification": {
            "_summary": {"all_passed": True, "n_verifiable": 2.0, "n_passed": 2.0, "n_failed": 0.0, "n_unknown": 0.0},
            "_warnings": [],
            "a": {"passed": True, "solver_success": True, "certificate": _certificate(True)},
            "b": {"passed": True, "solver_success": True, "certificate": {**_certificate(True), "kkt_stationarity_inf": 1.5e-10}},
        },
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
async def test_a_bare_certificate_is_not_reported_as_convergence(mcp_client):
    """The multistart idiom exports `best["certificate"]`, and a certificate is not a verdict.

    The shipped multistart example does exactly this: its workers return plain dicts across
    a process pool, so the result object never reaches `export()` and the payload is built
    from a certificate alone. `apply_certificate_veto` is one-way backend-side — it
    downgrades a solver success its certificate contradicts but never upgrades a failure —
    so a run that stopped at its iteration limit keeps `success=False`, and an empty
    `objective_value` with it, while the point it returned can still satisfy KKT. Calling
    that "converged" hands the agent an authoritative pass over numbers no solve claimed.
    """
    body = {
        "success": True,
        "result": {"best_variables": {"x": 1.0}, "n_successful": 3},
        "execution_time": 0.1,
        "verification": {
            "_summary": {"all_passed": True, "n_verifiable": 1, "n_passed": 1, "n_failed": 0, "n_unknown": 0},
            "_warnings": [],
            "best_certificate": {"passed": True, "certificate": _certificate(True), "diagnosis": None},
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('best_certificate', best['certificate'])"})

    verdict = _texts(response)[0]
    assert "Verification: certificate only" in verdict
    assert "Verification: passed" not in verdict
    assert "converged" not in verdict.split("not evidence that anything converged")[0]
    # Names the export it could not confirm, and what to export instead.
    assert "`best_certificate`" in verdict
    assert "'certificate': ..." in verdict


@pytest.mark.asyncio
async def test_a_result_exported_beside_its_own_certificate_still_passes(mcp_client):
    """The documented idiom exports both, and the backend counts them as the one solve.

    Serialization loses the object identity the backend deduped on, so the two entries are
    matched here by certificate content instead. Without that, the commonest export pattern
    in the codegen templates would lose its "converged" wording to its own second export.
    """
    certificate = _certificate(True)
    body = {
        "success": True,
        "result": {"result": {"success": True, "status": "Solve_Succeeded"}},
        "execution_time": 0.1,
        "verification": {
            "_summary": {"all_passed": True, "n_verifiable": 1, "n_passed": 1, "n_failed": 0, "n_unknown": 0},
            "_warnings": [],
            "result": {"passed": True, "solver_success": True, "solver_status": "Solve_Succeeded", "certificate": certificate},
            "certificate": {"passed": True, "certificate": certificate, "diagnosis": None},
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    assert "Verification: passed. All 1 exported solve(s)" in _texts(response)[0]


@pytest.mark.asyncio
async def test_a_stray_certificate_does_not_ride_on_another_solves_verdict(mcp_client):
    """Two counted solves, one verdict: the passing solve cannot vouch for the other one.

    This is the shape the headline has to refuse — a solve that really did converge beside
    a certificate belonging to something else, which the totals count as verified.
    """
    body = {
        "success": True,
        "result": {"result": {"success": True, "status": "Solve_Succeeded"}},
        "execution_time": 0.1,
        "verification": {
            "_summary": {"all_passed": True, "n_verifiable": 2, "n_passed": 2, "n_failed": 0, "n_unknown": 0},
            "_warnings": [],
            "result": {"passed": True, "solver_success": True, "certificate": _certificate(True)},
            "other_certificate": {
                "passed": True,
                "certificate": {**_certificate(True), "kkt_stationarity_inf": 7.1e-11},
                "diagnosis": None,
            },
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: certificate only" in verdict
    assert "Of 2 counted solve(s), 1 export(s) passed on a certificate alone" in verdict
    assert "`other_certificate`" in verdict


@pytest.mark.asyncio
async def test_a_stray_certificate_identical_to_a_proven_one_is_still_not_a_pass(mcp_client):
    """The counts catch what the content matching cannot tell apart.

    Two solves can produce byte-identical certificates — two starts converging to the same
    root — so matching a bare certificate to a proven one by content can credit it to the
    wrong solve. It cannot produce a false pass: identical content means either the one
    object the backend deduped, whose total is then 1, or a second solve the totals count
    separately and no solver verdict accounts for. Observed against the real producer, where
    two fixtures with the same residuals serialize identically.
    """
    certificate = _certificate(True)
    body = {
        "success": True,
        "result": {"result": {"success": True, "status": "Solve_Succeeded"}},
        "execution_time": 0.1,
        "verification": {
            "_summary": {"all_passed": True, "n_verifiable": 2, "n_passed": 2, "n_failed": 0, "n_unknown": 0},
            "_warnings": [],
            "result": {"passed": True, "solver_success": True, "certificate": certificate},
            "best_certificate": {"passed": True, "certificate": certificate, "diagnosis": None},
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: certificate only" in verdict
    assert "states a solver verdict for only 1 of them" in verdict


@pytest.mark.asyncio
async def test_a_multistart_of_results_reads_the_verdict_of_every_item(mcp_client):
    """One export, several solves: the verdicts live on `items`, not on the wrapper.

    The wrapper entry carries `certificate: None` by contract, so reading only the top level
    would find no solver verdict anywhere and downgrade a fully proven multistart.
    """
    body = {
        "success": True,
        "result": {"runs": [{"success": True}, {"success": True}]},
        "execution_time": 0.1,
        "verification": {
            "_summary": {"all_passed": True, "n_verifiable": 2, "n_passed": 2, "n_failed": 0, "n_unknown": 0},
            "_warnings": [],
            "runs": {
                "passed": True,
                "certificate": None,
                "diagnosis": None,
                "items": {
                    "0": {"passed": True, "solver_success": True, "certificate": _certificate(True)},
                    "1": {"passed": True, "solver_success": True, "certificate": {**_certificate(True), "complementarity_inf": 1e-09}},
                },
            },
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('runs', runs)"})

    assert "Verification: passed. All 2 exported solve(s)" in _texts(response)[0]


@pytest.mark.asyncio
async def test_counts_with_no_entry_behind_them_are_not_a_pass(mcp_client):
    """The totals can count a solve the payload shows no entry for, and a count is not proof.

    A reserved-key collision produces exactly this: an export named `_summary` is counted in
    the totals and reported nowhere else, so nothing in the payload states that solve's
    verdict.
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
        response = await mcp_client.call_tool("execute_code", {"code": "export('_summary', result)"})

    verdict = _texts(response)[0]
    assert "Verification: certificate only" in verdict
    assert "states a solver verdict for only 0 of them" in verdict
    # The advisory that explains the shape still travels.
    assert "collides with a reserved verification key" in verdict


@pytest.mark.asyncio
async def test_a_failed_solver_verdict_beside_a_pass_flag_is_not_a_pass(mcp_client):
    """The entry's own flags outrank the totals, in the safe direction only."""
    body = {
        "success": True,
        "result": {"result": {"success": False, "status": "Maximum_Iterations_Exceeded"}},
        "execution_time": 0.1,
        "verification": {
            "_summary": {"all_passed": True, "n_verifiable": 1, "n_passed": 1, "n_failed": 0, "n_unknown": 0},
            "_warnings": [],
            "result": {
                "passed": True,
                "solver_success": False,
                "solver_status": "Maximum_Iterations_Exceeded",
                "certificate": _certificate(True),
            },
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: NOT passed" in verdict
    assert "Do not report these numbers as the answer" in verdict


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("summary", "reason"),
    [
        # Nobody said whether anything failed. A count that was never sent is not a zero.
        ({"all_passed": True, "n_verifiable": 1, "n_passed": 1}, "n_failed=None"),
        # A count that is not a number cannot be read as one.
        ({"all_passed": True, "n_verifiable": 1, "n_passed": 1, "n_failed": "1", "n_unknown": 0}, "n_failed='1'"),
        # The totals contradict themselves: one solve accounted for out of two.
        ({"all_passed": True, "n_verifiable": 2, "n_passed": 1, "n_failed": 0, "n_unknown": 0}, "n_verifiable=2"),
        # Negative is not a count either.
        ({"all_passed": True, "n_verifiable": 1, "n_passed": 1, "n_failed": -1, "n_unknown": 0}, "n_failed=-1"),
    ],
)
async def test_a_summary_whose_counts_cannot_be_read_is_inconclusive(mcp_client, summary, reason):
    """`verification` is an open dict, so the pass path has to require valid, consistent counts.

    Each of these used to certify a pass: the counts were normalized to 0 and the zero then
    read as evidence that nothing failed. An unreadable summary is not a finding either —
    nothing here says a solve went wrong — so the verdict says what could not be read.
    """
    body = {
        "success": True,
        "result": {"result": {}},
        "execution_time": 0.1,
        "verification": {
            "_summary": summary,
            "_warnings": [],
            "result": {"passed": True, "solver_success": True, "certificate": _certificate(True)},
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"})

    verdict = _texts(response)[0]
    assert "Verification: inconclusive" in verdict
    assert "Verification: passed" not in verdict
    # The verdict quotes the counts as they arrived, so the shape is debuggable from the text.
    assert reason in verdict


# ── execute_code: the code itself failing ────────────────────────────────────


@pytest.mark.asyncio
async def test_code_that_did_not_run_is_an_error_not_an_unverified_answer(mcp_client):
    """`isError` separates a crash from a result, and a host acts on that distinction.

    Reported as a normal result, a run that never happened files next to a solved one. The
    live api answers a crash with a 4xx that the tool's `except` already raises on, so this
    branch covers a 200 whose body says the code did not run.
    """
    body = {"success": False, "result": None, "error": "SyntaxError: invalid syntax", "stdout": "partial\n"}

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export("}, raise_on_error=False)

    assert response.is_error
    blob = _blob(response)
    assert "Execution failed: SyntaxError: invalid syntax" in blob
    assert "partial" in blob
    # No verdict line: nothing ran, so there is nothing to have verified.
    assert "Verification:" not in blob


@pytest.mark.asyncio
async def test_a_failing_certificate_on_a_run_that_completed_is_still_not_an_error(mcp_client):
    """The other half of the same distinction, asserted next to it so neither drifts.

    The code ran, so the exports, the certificate and the diagnosis are the answer to the
    call — raising would throw away exactly what fixes the problem.
    """
    with patch.object(ArgminService, "execute_code", return_value=_unverified_response()):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"}, raise_on_error=False)

    assert not response.is_error
    assert "Verification: NOT passed" in _texts(response)[0]


@pytest.mark.asyncio
async def test_a_verification_payload_on_a_failed_run_still_reaches_the_caller(mcp_client):
    """Raising drops `structured_content`, so anything diagnostic has to be in the message.

    The verdict text names per-export certificates and `diagnosis.suggestion` as the thing
    to act on, so the payload holding them has to arrive on this path too — the verdict line
    and `_warnings` alone would point at evidence that never came.
    """
    body = {
        "success": False,
        "result": {"result": {"success": False, "status": "Infeasible"}},
        "error": "TimeoutError: exceeded",
        "verification": {
            "_summary": {"all_passed": False, "n_verifiable": 1, "n_failed": 1},
            "_warnings": ["result: diverged"],
            "result": {
                "passed": False,
                "certificate": _certificate(False),
                "diagnosis": {"kind": "diverged", "suggestion": "Tighten the initial guess."},
            },
        },
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        response = await mcp_client.call_tool("execute_code", {"code": "export('result', result)"}, raise_on_error=False)

    assert response.is_error
    blob = _blob(response)
    assert "Execution failed: TimeoutError: exceeded" in blob
    assert "Verification: NOT passed" in blob
    assert "result: diverged" in blob
    # The evidence the verdict line sends the reader after, recoverable from the message.
    recovered = json.loads(next(line for line in blob.splitlines() if line.lstrip().startswith("{")))
    assert recovered == body
    entry = recovered["verification"]["result"]
    assert entry["certificate"]["kkt_stationarity_inf"] == 3.0
    assert entry["diagnosis"]["suggestion"] == "Tighten the initial guess."


@pytest.mark.asyncio
async def test_the_verdict_text_never_promises_a_payload_that_did_not_travel(mcp_client):
    """The claim `_verification_text` makes has to hold on both exits, not just the happy one.

    It tells the reader to read `verification` "in this response"; on the raising path there
    is no `structured_content` and no separate JSON block, so the dump has to ride the
    message or the instruction is false.
    """
    body = {
        "success": False,
        "error": "boom",
        "verification": {"_summary": {"all_passed": False, "n_verifiable": 1, "n_failed": 1}, "_warnings": []},
    }

    with patch.object(ArgminService, "execute_code", return_value=body):
        failing = await mcp_client.call_tool("execute_code", {"code": "..."}, raise_on_error=False)
    with patch.object(ArgminService, "execute_code", return_value=_unverified_response()):
        completed = await mcp_client.call_tool("execute_code", {"code": "..."}, raise_on_error=False)

    for response in (failing, completed):
        blob = _blob(response)
        assert "Read the `verification` payload in this response" in blob
        assert json.loads(next(line for line in blob.splitlines() if line.lstrip().startswith("{")))["verification"]
