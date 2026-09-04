"""AxArgmin MCP server — generate and run argmin numerical solves."""

from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import ContentBlock, TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .services.argmin_service import ArgminService

INSTRUCTIONS = """\
This server provides tools for numerical optimization, rootfinding, ODE simulation, and optimal control
using the argmin library. Use generate_code to produce executable code from a problem description,
then execute_code to run it in a sandboxed environment.

READING A RESULT: `success` says only that the code RAN. Whether the *answers* are solved is reported
separately, in the `verification` payload execute_code returns alongside the exports. A diverged or
infeasible solve runs perfectly cleanly and comes back with `success: true`.

- `verification._summary.all_passed` is the flag to read. It is true only when every exported solve both
  converged and produced a certificate that passed at the requested tolerances.
- Where the two disagree, the `Verification:` line in the tool's text output wins over the raw flag in the
  structured result. That line is not a copy of `all_passed`: it reports a pass only when the payload also
  counted at least one solve AND counted none as failed or unverified. So a payload claiming a pass over
  nothing checked, or claiming one beside a non-zero `n_failed`/`n_unknown`, is reported as unverified
  rather than certified. Nothing is hidden — the full payload is in the structured result either way.
- `verification._warnings` names findings: what did not check out, and by how much, per export. It may also
  carry an advisory that does not bear on the verdict — an export name colliding with a reserved key, say —
  so a warning is not by itself a failure. The `Verification:` line is what says whether it mattered.
- Each entry also carries the `certificate` (the KKT / residual / integration-accuracy check re-evaluated
  at the point actually returned) and, on failure, a `diagnosis` whose `kind` names the failure class and
  whose `suggestion` says what to change. Pass those on to the user rather than only that it failed.

When a solve does not verify, do NOT report its numbers as the answer, and do not quietly simplify the
problem until something converges — dropping constraints or coarsening the discretisation yields a
confident answer to a different question. Fix the formulation or the solver settings, or report the failure.

To get a certificate back, the generated code only has to export the result object itself
(`export('result', result)`); the certificate and diagnosis travel with it.
"""

mcp = FastMCP(
    name="AxArgmin Server",
    instructions=INSTRUCTIONS + get_feedback_prompt(["generate_code", "execute_code"]),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)

argmin_service = ArgminService()

# No `output_schema` here, deliberately. fastmcp builds the client's `.data` from the
# declared schema, keeping only what the schema names: declaring one for `verification`
# reduced `.data` to `_summary` and `_warnings` and dropped every per-export certificate
# and diagnosis — the payload this tool exists to deliver. An `additionalProperties`
# clause did not save the nested entries either, and constraining it to objects made a
# reserved key of any other type fail validation outright, taking the whole call with it.
# The backend types this field `dict[str, Any]` precisely so new certificate fields reach
# callers without an SDK or MCP release; a JSON Schema here fights that. The shape is
# documented in the tool description and the server instructions instead, which is where
# a model reads it anyway.
_NOTHING_EXPORTED_TEXT = (
    "Verification: none. No export carried a solver result, so no certificate came back and nothing about "
    "this answer has been checked. Export the result object itself — export('result', result) — and the "
    "certificate travels with it."
)
_BACKEND_TOO_OLD_TEXT = (
    "Verification: unavailable. A solver result was exported, but this deployment of the argmin executor "
    "predates the certificate payload, so the answer has not been independently checked. The code is fine — "
    "do not rewrite it. Read the solver result in the exports — its own `success` and `status` fields — and "
    "say the answer is unverified when you report it."
)

# A serialized solver result is recognised by the fields every argmin result carries, rather
# than by its export name, which the generated code chooses freely.
_SOLVER_RESULT_MARKERS = ("success", "status")
# The executor walks containers to find results; so must this, or a multistart export
# (a list of results, a dict of per-start records) reads as "nothing was exported".
# Bounded so that a long trajectory export cannot make the scan expensive.
_EXPORT_SCAN_DEPTH = 3


def _text(message: str) -> TextContent:
    return TextContent(type="text", text=message)


def _count(value: Any) -> int:
    """A count from the payload, or 0 when it is missing or not a whole number.

    Accepts 2.0 as well as 2: the field is typed `dict[str, Any]` backend-side and JSON
    makes no distinction, so rejecting the float would silently downgrade a genuinely
    verified pass to "inconclusive". A fractional count is not a count, and fails closed.
    """
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return 0


def _exported_a_solver_result(exports: Any, _depth: int = 0) -> bool:
    """Whether anything in the exports is a serialized solver result.

    Never tests the exports mapping itself (`_depth` 0): code that calls
    `export('success', ...)` and `export('status', ...)` separately — the optimal-control
    examples do — would otherwise make the whole mapping look like one result.
    """
    if _depth and isinstance(exports, dict) and all(marker in exports for marker in _SOLVER_RESULT_MARKERS):
        return True
    if _depth >= _EXPORT_SCAN_DEPTH:
        return False
    if isinstance(exports, dict):
        children: Any = exports.values()
    elif isinstance(exports, (list, tuple)):
        children = exports
    else:
        return False
    return any(_exported_a_solver_result(child, _depth + 1) for child in children)


def _verification_text(verification: Any, exports: Any = None) -> str:
    """One block saying whether the answers are solved, not merely whether the code ran.

    Reporting only, never blocking: a failed certificate is described here and does not turn the
    call into an error. Solves that fail are a normal part of working a problem, and raising would
    throw away the exports, the diagnosis and the certificate — exactly what the caller needs to
    fix it.
    """
    if not isinstance(verification, dict) or not verification:
        # A missing payload has two causes the response cannot tell apart, and telling an agent
        # the wrong one is costly: "export the result" sends it rewriting code that was already
        # correct. Attribute it from the exports instead — a current executor walking an exported
        # result object always produces a payload, so a serialized solver result sitting next to a
        # missing payload can only be the older backend.
        return _BACKEND_TOO_OLD_TEXT if _exported_a_solver_result(exports) else _NOTHING_EXPORTED_TEXT

    summary = verification.get("_summary")
    summary = summary if isinstance(summary, dict) else {}
    checked = _count(summary.get("n_verifiable"))
    warnings = verification.get("_warnings")
    warnings = warnings if isinstance(warnings, list) else []

    failed = _count(summary.get("n_failed"))
    unknown = _count(summary.get("n_unknown"))

    # Computed BEFORE the pass branch, so a self-inconsistent payload cannot be certified
    # on its flag alone. `all_passed` is defined backend-side as `n_failed == 0 and
    # n_unknown == 0`, so a true flag beside a positive count is a contradiction, and the
    # safe reading of a contradiction about whether an answer is solved is that it is not.
    #
    # A warning is deliberately NOT disqualifying. `_warnings_for` returns nothing for a
    # passing entry, so per-entry lines are findings — but the reserved-key collision
    # warning is emitted whether or not the colliding export passed, so an advisory beside
    # a clean run is a real shape today. Downgrading on it would fail a legitimate pass;
    # instead the advisory is carried into the pass text rather than swallowed.
    contradicts_a_pass = failed or unknown

    if summary.get("all_passed") is True and checked > 0 and not contradicts_a_pass:
        passed_lines = [
            f"Verification: passed. All {checked} exported solve(s) converged and satisfied their certificate " f"at the requested tolerances."
        ]
        if warnings:
            passed_lines.append("The payload also notes:")
            passed_lines.extend(f"  - {warning}" for warning in warnings)
        return "\n".join(passed_lines)

    # Anything the payload says went wrong is a finding, even when the counts are missing
    # or a shape this server does not know. Falling back to "inconclusive" here would drop
    # the warnings naming what missed and by how much, and with them the instruction not to
    # report the numbers -- the strongest thing this block says, lost exactly when it applies.
    states_a_failure = summary.get("all_passed") is False or contradicts_a_pass or warnings
    if not states_a_failure:
        return (
            "Verification: inconclusive. A payload came back but reports no checked solve and no finding, so "
            "nothing about this answer has been certified. Treat it as unverified and say so when you report it."
        )

    # Phrased from what is actually known: "of 3 checked solve(s) 0 failed and 0 produced
    # none" would contradict the headline it sits under when a warning drove the verdict.
    if failed or unknown:
        counts = (
            f"of {checked} checked solve(s) {failed} failed their certificate and {unknown} produced none"
            if checked > 0
            else f"{failed} solve(s) failed their certificate and {unknown} produced none"
        )
    elif checked > 0:
        counts = f"none of the {checked} checked solve(s) is counted as failed, though the payload reports findings"
    else:
        counts = "the payload reports findings without counting them"
    lines = [f"Verification: NOT passed. The code ran, but {counts}."]
    lines.extend(f"  - {warning}" for warning in warnings)
    lines.append(
        "Do not report these numbers as the answer, and do not simplify the problem until it converges. "
        "Read `verification` in the structured result for each certificate and diagnosis — `diagnosis.suggestion` "
        "says what to change — then fix the formulation or the solver settings and re-run."
    )
    return "\n".join(lines)


@mcp.tool(
    name="generate_code",
    description=(
        "Generate Python code to solve a numerical problem using the argmin library. "
        "Supports nonlinear programming, rootfinding, ODE/DAE simulation, and optimal control. "
        "Returns executable code and an explanation of the approach. "
        "The code must be executed separately using the execute_code tool."
    ),
    tags=["argmin", "optimization", "code-generation"],
)
async def generate_code(
    problem_description: Annotated[str, "Natural language or mathematical description of the problem"],
    problem_type: Annotated[
        str,
        "Problem type: 'nonlinear_program' (minimize f(x) s.t. constraints), "
        "'nonlinear_equations' (solve F(x)=0, rootfinding), "
        "'initial_value_problem' (integrate dx/dt=f(x,t), ODE/DAE), "
        "or 'optimal_control' (dynamic optimization over time)",
    ],
) -> ToolResult:
    """Generate Python code for a numerical problem using the argmin library."""
    valid_types = {"nonlinear_program", "nonlinear_equations", "initial_value_problem", "optimal_control"}
    if problem_type not in valid_types:
        raise ToolError(f"Invalid problem_type '{problem_type}'. Must be one of: {', '.join(sorted(valid_types))}")

    try:
        response = argmin_service.generate_code(problem_description, problem_type)
    except Exception as e:
        raise ToolError(f"Failed to generate code: {e!s}") from e

    if response.get("error"):
        return ToolResult(content=[_text(f"Code generation failed: {response['error']}")])

    content: list[ContentBlock] = []
    if response.get("explanation"):
        content.append(_text(response["explanation"]))
    if response.get("code"):
        content.append(_text(f"```python\n{response['code']}\n```"))

    return ToolResult(
        content=content,
        structured_content=response,
    )


@mcp.tool(
    name="execute_code",
    description=(
        "Execute Python code in a sandboxed environment with numpy, math, and the ax_core.argmin "
        "numerical library available. Code must call export(name, value) at least once to return results. "
        "Typically used to run code produced by the generate_code tool, but also accepts hand-written or modified code. "
        "Returns the exports plus a `verification` payload holding the certificate and diagnosis of every exported "
        "solver result: `success` reports only that the code ran, so read the `Verification:` line in the response "
        "to learn whether the answers are solved."
    ),
    tags=["argmin", "execution", "sandbox"],
)
async def execute_code(
    code: Annotated[str, "Python code to execute. Must call export(name, value) to return results."],
) -> ToolResult:
    """Execute Python code in the argmin sandbox."""
    try:
        response = argmin_service.execute_code(code)
    except Exception as e:
        raise ToolError(f"Failed to execute code: {e!s}") from e

    if not response.get("success"):
        error_msg = response.get("error", "Unknown execution error")
        stdout = response.get("stdout", "")
        text = f"Execution failed: {error_msg}"
        if stdout:
            text += f"\n\nStdout:\n{stdout}"
        failed: list[ContentBlock] = [_text(text)]
        # Today the executor only attaches a payload to a run that completed, so there is
        # nothing to report here. Conditional rather than absent so that if a partial
        # failure ever carries one, its certificates reach the model instead of being
        # dropped on the floor by this branch.
        if isinstance(response.get("verification"), dict) and response["verification"]:
            failed.append(_text(_verification_text(response["verification"], response.get("result"))))
        return ToolResult(content=failed, structured_content=response)

    # The verdict leads, so it frames the numbers that follow rather than trailing them:
    # a diverged solve returns `success: true` with empty trajectories, and read in the
    # other order the exports look like an answer.
    parts: list[ContentBlock] = [_text(_verification_text(response.get("verification"), response.get("result")))]
    if response.get("result"):
        parts.append(_text(f"Result: {response['result']}"))
    if response.get("stdout"):
        parts.append(_text(f"Stdout:\n{response['stdout']}"))
    execution_time = response.get("execution_time")
    if isinstance(execution_time, (int, float)) and not isinstance(execution_time, bool):
        parts.append(_text(f"Execution time: {execution_time:.3f}s"))

    return ToolResult(
        content=parts,
        structured_content=response,
    )
