"""AxArgmin MCP server — generate and run argmin numerical solves."""

import json
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import ContentBlock, TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .services.argmin_service import ArgminService

# Kept to the one thing a caller has to know on every turn: read the verdict line, and what to do
# when it is not a pass. The shape of the `verification` payload behind that line is detail for the
# call itself, so it lives on the execute_code description rather than in the system prompt.
INSTRUCTIONS = """\
This server provides tools for numerical optimization, rootfinding, ODE simulation, and optimal control
using the argmin library. Use generate_code to produce executable code from a problem description,
then execute_code to run it in a sandboxed environment.

READING A RESULT: `success` says only that the code RAN — a diverged or infeasible solve runs perfectly
cleanly and comes back with `success: true`. Whether the *answers* are solved is the `Verification:` line
that leads execute_code's output. Read that line and treat it as the verdict. It certifies the result only
when every exported solve converged and satisfied its certificate; anything else — NOT passed,
certificate only, inconclusive, none — means the answer is not certified.

When a solve does not verify, do NOT report its numbers as the answer, and do not quietly simplify the
problem until something converges — dropping constraints or coarsening the discretisation yields a
confident answer to a different question. Fix the formulation or the solver settings, or report the failure.

The evidence behind the verdict — per exported solve, a certificate, a diagnosis and a suggested fix —
comes back in the `verification` payload, whose shape the execute_code tool describes. Pass that detail on
to the user rather than only the fact that something failed.
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
# documented on the execute_code tool instead, which is where a model reads it anyway, and
# the payload also goes out as a JSON text block so a client that ignores `.data` keeps it.
_NO_PAYLOAD_TEXT = (
    "Verification: none. No certificate came back with this run, so nothing about this answer has been "
    "independently checked. Two things produce that and this response cannot tell them apart: no export carried "
    "a solver result or a certificate for the executor to collect, or this deployment of the executor predates "
    "the certificate payload. Export the result object itself — export('result', result) — and if a certificate "
    "still does not come back, read the solver result's own `success` and `status` fields in the exports and say "
    "the answer is unverified when you report it."
)

# The keys the payload reserves for itself. Everything else at its top level is a per-export
# entry, which is what a verdict about a *solve* has to be read from.
_RESERVED_KEYS = ("_summary", "_warnings")
# Cap on how many exports the certificate-only verdict names, so a 30-start multistart of
# bare certificates cannot bury the two sentences that say what to do about it.
_MAX_NAMED_UNPROVEN = 5


def _text(message: str) -> TextContent:
    return TextContent(type="text", text=message)


def _json_text(response: dict[str, Any]) -> str:
    """The whole response as JSON.

    Dumped whole rather than field-picked, so it cannot drift from `structured_content`,
    and unindented: an optimal-control run exports a few thousand trajectory floats, and
    `indent=2` would put each on its own line. `default=str` is only so that a value which
    somehow will not serialize costs this text rather than the whole response — the verdict
    and the exports are already out by then.

    Shared by both exits, because `_verification_text` tells the reader the payload is in
    this response and that has to hold on the raising path too, where there is no
    `structured_content` to fall back on.
    """
    return json.dumps(response, default=str)


def _json_block(response: dict[str, Any]) -> TextContent:
    """The whole response as JSON, in a text block beside `structured_content`.

    MCP asks a tool that returns structured content to also return the serialized JSON in
    a text block, because a client is free to ignore `structuredContent` — and the ones
    that do show a model only the content blocks. For this tool that field is the payload:
    the per-export certificates and diagnoses reach the caller nowhere else, and the
    readable blocks around this one carry the verdict but not the numbers behind it.
    """
    return _text(_json_text(response))


def _count(value: Any) -> int | None:
    """A count from the payload, or None when it is missing or not a whole number >= 0.

    Accepts 2.0 as well as 2: the field is typed `dict[str, Any]` backend-side and JSON
    makes no distinction, so rejecting the float would silently downgrade a genuinely
    verified pass to "inconclusive". A fractional or negative count is not a count.

    None rather than 0, because the two readings differ exactly where it matters: an absent
    or unreadable `n_failed` is not evidence that nothing failed. Mapping it to 0 let a
    summary claiming `all_passed` with no failure counts at all — or with `n_failed: "1"` —
    certify a pass on the strength of a field that was never read.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float) and value.is_integer() and value >= 0:
        return int(value)
    return None


def _entries(verification: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Every per-export entry in the payload, labelled, with `items` flattened.

    An export holding several verifiable objects — a list of results, a dict of multistart
    records — carries its finds under `items` and leaves its own `certificate` and
    `diagnosis` None, so there the items are the entries and the wrapper is not one.
    """
    found: list[tuple[str, dict[str, Any]]] = []
    for name, entry in verification.items():
        if name in _RESERVED_KEYS or not isinstance(entry, dict):
            continue
        items = entry.get("items")
        if isinstance(items, dict):
            found.extend((f"{name}.{key}", item) for key, item in items.items() if isinstance(item, dict))
        else:
            found.append((name, entry))
    return found


def _certificate_key(certificate: Any) -> str | None:
    """A comparable identity for a certificate, or None when there is none.

    The backend dedupes entries by object identity, which serialization loses, so two
    entries holding one certificate are recognised here by its content instead. Content
    equality credits a bare certificate to a solve whose verdict is known whenever the two
    agree to the last digit of every residual and tolerance — either the same solve, or
    indistinguishable from it in everything this response can see.
    """
    if certificate is None:
        return None
    return json.dumps(certificate, sort_keys=True, default=str)


def _convergence_proof(entries: list[tuple[str, dict[str, Any]]]) -> tuple[int, list[str]]:
    """How many entries state a successful solver verdict, and which entries state none.

    A certificate is not a substitute for that verdict. `apply_certificate_veto` is one-way
    backend-side: it downgrades a solver success its certificate contradicts but never
    upgrades a failure, so a run that stopped at its iteration limit keeps `success=False`,
    and an empty `objective_value` with it, while the point it returned can still satisfy
    KKT. A payload assembled only from certificates therefore says nothing about whether
    anything converged — and the documented multistart idiom, which exports
    `best['certificate']` because the result object never survives the process pool,
    produces exactly that.

    An entry whose certificate is also carried by an entry that *does* state a verdict is
    not counted as missing one: `export('result', r)` beside `export('certificate',
    r.certificate)` is the documented idiom, and the backend already counts the pair as the
    one solve it is.
    """
    with_verdict = [entry for _, entry in entries if entry.get("solver_success") is True]
    proven = {key for entry in with_verdict if (key := _certificate_key(entry.get("certificate"))) is not None}
    unproven = [
        label for label, entry in entries if entry.get("solver_success") is not True and _certificate_key(entry.get("certificate")) not in proven
    ]
    return len(with_verdict), unproven


def _named(labels: list[str]) -> str:
    """The first few labels, and how many more there are."""
    shown = ", ".join(f"`{label}`" for label in labels[:_MAX_NAMED_UNPROVEN])
    remainder = len(labels) - _MAX_NAMED_UNPROVEN
    return f"{shown}, and {remainder} more" if remainder > 0 else shown


def _with_advisories(lines: list[str], warnings: list[Any]) -> str:
    """Verdict lines, plus any warnings the payload carried alongside them.

    Only ever reached from a verdict the payload states no failure for, so a warning here is
    an advisory — the reserved-key collision, say — and is carried through rather than
    swallowed, without being read as a finding.
    """
    if warnings:
        lines = [*lines, "The payload also notes:", *(f"  - {warning}" for warning in warnings)]
    return "\n".join(lines)


def _verification_text(verification: Any) -> str:
    """One block saying whether the answers are solved, not merely whether the code ran.

    Reporting only, never blocking: a failed certificate is described here and does not turn the
    call into an error. Solves that fail are a normal part of working a problem, and raising would
    throw away the exports, the diagnosis and the certificate — exactly what the caller needs to
    fix it.
    """
    if not isinstance(verification, dict) or not verification:
        # Two causes, and nothing in the response separates them: a current executor returns
        # no payload whenever no export carried something verifiable, and one that predates
        # the payload returns none either way. Sniffing the exports for something
        # result-shaped used to pick between them and was wrong in both directions — a plain
        # `{"success": ..., "status": ...}` mapping with no certificate in it is precisely
        # what a *current* backend returns no payload for, while a bare exported certificate
        # is not result-shaped at all — and the executor also degrades to no payload when
        # collecting one fails. Naming the wrong cause costs more than naming none, because
        # each cause carries an instruction: "the code is fine, do not rewrite it" is wrong
        # whenever the export really was the problem. Backend age needs an explicit
        # capability signal, and the response carries none today.
        return _NO_PAYLOAD_TEXT

    summary = verification.get("_summary")
    summary = summary if isinstance(summary, dict) else {}
    warnings = verification.get("_warnings")
    warnings = warnings if isinstance(warnings, list) else []

    checked = _count(summary.get("n_verifiable"))
    counted_passed = _count(summary.get("n_passed"))
    failed = _count(summary.get("n_failed"))
    unknown = _count(summary.get("n_unknown"))
    # All four counts have to be present, readable and add up before any one of them can be
    # read as evidence that nothing failed: a zero that was never sent is not a zero. The
    # backend sends all four whenever it sends a payload at all, so the whole cost of this
    # strictness falls on payloads that are already self-contradictory, where the honest
    # verdict is that nothing is certified.
    counts_add_up = (
        checked is not None
        and counted_passed is not None
        and failed is not None
        and unknown is not None
        and counted_passed + failed + unknown == checked
    )

    entries = _entries(verification)
    with_verdict, unproven = _convergence_proof(entries)
    # A solve counted in the totals but shown in no readable entry is unproven too: an
    # export named `_summary` collides with a reserved key and is reported only in the
    # totals, and a count with nothing behind it certifies nothing.
    #
    # This also closes the one hole in the content matching above. A bare certificate whose
    # content coincides with a proven one is either the same object -- which the backend
    # deduped, so the totals count the single solve it is and this stays 0 -- or a second
    # object, which the totals count separately and no verdict accounts for, so this
    # catches it whether or not the two certificates were told apart.
    unbacked = max((checked or 0) - with_verdict, 0)

    # Computed BEFORE the pass branch, so a self-inconsistent payload cannot be certified
    # on its flag alone. `all_passed` is defined backend-side as `n_failed == 0 and
    # n_unknown == 0`, so a true flag beside a positive count is a contradiction, and the
    # safe reading of a contradiction about whether an answer is solved is that it is not.
    # An entry stating a failure of its own is read the same way, whatever the totals say.
    #
    # A warning is deliberately NOT disqualifying. `_warnings_for` returns nothing for a
    # passing entry, so per-entry lines are findings — but the reserved-key collision
    # warning is emitted whether or not the colliding export passed, so an advisory beside
    # a clean run is a real shape today. Downgrading on it would fail a legitimate pass;
    # instead the advisory is carried into the verdict text rather than swallowed.
    counted_failures = bool(failed) or bool(unknown)
    entry_failures = any(entry.get("passed") is False or entry.get("solver_success") is False for _, entry in entries)

    if summary.get("all_passed") is True and counts_add_up and bool(checked) and not counted_failures and not entry_failures:
        if not unproven and not unbacked:
            return _with_advisories(
                [f"Verification: passed. All {checked} exported solve(s) converged and satisfied their certificate at the requested tolerances."],
                warnings,
            )
        # Pass-shaped, but the payload never states that the solver itself succeeded — so the
        # one thing this line must not say is that anything converged.
        if unproven:
            detail = (
                f"Of {checked} counted solve(s), {len(unproven)} export(s) passed on a certificate alone "
                f"({_named(unproven)}) with nothing in the payload stating that the solver itself succeeded there."
            )
        else:
            detail = (
                f"The payload counts {checked} verifiable solve(s) but states a solver verdict for only "
                f"{with_verdict} of them, so the rest are certified by a count with no entry behind it."
            )
        return _with_advisories(
            [
                f"Verification: certificate only. {detail} A certificate can pass at the point a failed solve "
                "returned — that point can satisfy KKT while the solver stopped at its iteration limit and left "
                "`objective_value` empty — so this is not evidence that anything converged.",
                "Read `success` and `status` on the results in the exports before reporting these numbers, and "
                "report the answer as certificate-checked but unconfirmed. To get the full verdict, export the "
                "result object itself — export('result', result) — or, where it cannot reach export (a multistart "
                "across a process pool), export the whole record beside its certificate "
                "({'success': ..., 'status': ..., 'certificate': ...}) so the solver's own verdict travels with it.",
            ],
            warnings,
        )

    # Anything the payload says went wrong is a finding, even when the counts are missing
    # or a shape this server does not know. Falling back to "inconclusive" here would drop
    # the warnings naming what missed and by how much, and with them the instruction not to
    # report the numbers -- the strongest thing this block says, lost exactly when it applies.
    if not (summary.get("all_passed") is False or counted_failures or entry_failures or warnings):
        # Nothing is contradicted here, only missing, so the verdict says what could not be
        # read rather than implying a finding the payload never reported.
        reasons = []
        if not counts_add_up:
            reasons.append(
                "its `_summary` counts are missing, unreadable or do not add up "
                f"(n_verifiable={summary.get('n_verifiable')!r}, n_passed={summary.get('n_passed')!r}, "
                f"n_failed={summary.get('n_failed')!r}, n_unknown={summary.get('n_unknown')!r})"
            )
        if not isinstance(summary.get("all_passed"), bool):
            reasons.append(f"`_summary.all_passed` is {summary.get('all_passed')!r} rather than a bool")
        if counts_add_up and not checked:
            reasons.append("it counts no verifiable solve and reports no finding")
        if not reasons:
            reasons.append("it states no verdict this response can read as evidence")
        return (
            f"Verification: inconclusive. A payload came back, but {'; '.join(reasons)}. Nothing about this answer "
            "has been certified, so treat it as unverified and say so when you report it."
        )

    # Phrased from what is actually known: naming a count the payload did not send would
    # claim knowledge this verdict has just refused to claim, and "of 0 checked solve(s) 2
    # failed" would contradict the headline it sits under.
    if failed or unknown:
        parts = []
        if failed:
            # Not "failed their certificate": `n_failed` also counts the solver-failure
            # downgrade, where the certificate passed at the point returned and the solve
            # is what did not hold. The `_warnings` line below names which of the two it
            # was, per entry, so this sentence does not have to guess.
            parts.append(f"{failed} did not verify")
        if unknown:
            parts.append(f"{unknown} produced no certificate")
        counts = f"of {checked} checked solve(s) {' and '.join(parts)}" if checked else f"{' and '.join(parts)} (out of an unreported total)"
    elif checked:
        counts = f"none of the {checked} checked solve(s) is counted as failed, though the payload reports findings"
    else:
        counts = "the payload reports findings without counting them"
    lines = [f"Verification: NOT passed. The code ran, but {counts}."]
    if not counts_add_up:
        lines.append("  - the `_summary` counts are missing, unreadable or do not add up, so the totals above are only what could be read")
    lines.extend(f"  - {warning}" for warning in warnings)
    lines.append(
        "Do not report these numbers as the answer, and do not simplify the problem until it converges. "
        "Read the `verification` payload in this response for each certificate and diagnosis — `diagnosis.suggestion` "
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
        "Typically used to run code produced by the generate_code tool, but also accepts hand-written or modified code.\n\n"
        "`success` reports only that the code ran. The `Verification:` line leading the response is the verdict on "
        "whether the answers are solved; read it first. The response also carries the exports and, from a backend that "
        "supports it, a `verification` payload holding the certificate and diagnosis of every exported solver result — "
        "both as structured content and as a JSON text block.\n\n"
        "Reading `verification` for the detail behind the verdict line:\n"
        "- `_summary.all_passed` is an input to that line, not a substitute for it. The line reports a pass only when "
        "the summary's four counts are all present, readable and adding up, at least one solve was counted, none was "
        "counted as failed or unverified, AND the per-export entries show a successful `solver_success` behind every "
        "solve counted. So a payload claiming a pass over nothing checked, beside a non-zero `n_failed`/`n_unknown`, "
        "with counts that cannot be read, or on certificates alone is reported as unverified. Where the two disagree, "
        "the line wins.\n"
        "- a certificate is not a solver verdict. An export carrying a bare certificate — the multistart idiom "
        "`export('best_certificate', best['certificate'])` — gets `Verification: certificate only`: the certificate "
        "passed at the point returned, but a failed solve's certificate can pass there too, so nothing says the solve "
        "converged. Export the result object, or the whole record `{'success': ..., 'status': ..., 'certificate': ...}`, "
        "to get the verdict as well.\n"
        "- `_warnings` names what did not check out, and by how much, per export. It may also carry an advisory that "
        "does not bear on the verdict — an export name colliding with a reserved key, say — so a warning is not by "
        "itself a failure.\n"
        "- each per-export entry carries the `certificate` (the KKT / residual / integration-accuracy check "
        "re-evaluated at the point actually returned) and, on failure, a `diagnosis` whose `kind` names the failure "
        "class and whose `suggestion` says what to change. Pass those on rather than only that it failed.\n"
        "- to get a certificate back at all, the code only has to export the result object itself "
        "(`export('result', result)`); the certificate and diagnosis travel with it."
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
        # The code did not run, so this is a failed call and not an unverified answer: a host
        # that reads `isError` must not file a crash next to a solved result. A failing
        # *certificate* on a run that completed is the opposite case and stays a normal result
        # further down — the exports and the diagnosis are the whole point there.
        #
        # Raising is the only way to set `isError` under fastmcp: `ToolResult` carries no such
        # field, and the manager sets the flag from the exception. That drops
        # `structured_content`, so everything the caller needs goes into the message; a
        # `ToolError` reaches the client verbatim and is never masked.
        #
        # In practice the api answers a crash with a 4xx and the `except` above already
        # reports it, so this branch only fires on a 200 that says the code did not run.
        failed = [f"Execution failed: {response.get('error') or 'Unknown execution error'}"]
        if response.get("stdout"):
            failed.append(f"Stdout:\n{response['stdout']}")
        # Today the executor only attaches a payload to a run that completed, so there is
        # nothing to report here. Conditional rather than absent so that if a partial
        # failure ever carries one, its verdict reaches the model instead of being dropped
        # on the floor by this branch.
        if isinstance(response.get("verification"), dict) and response["verification"]:
            failed.append(_verification_text(response["verification"]))
        # The message is the only channel left: raising drops `structured_content`, and there
        # are no content blocks to put a JSON one beside. Without this the verdict text above
        # would point at per-export certificates and a `diagnosis.suggestion` that never
        # arrived, having named them as the thing to act on.
        failed.append(_json_text(response))
        raise ToolError("\n\n".join(failed))

    # The verdict leads, so it frames the numbers that follow rather than trailing them:
    # a diverged solve returns `success: true` with empty trajectories, and read in the
    # other order the exports look like an answer.
    parts: list[ContentBlock] = [_text(_verification_text(response.get("verification")))]
    # Replaces a `Result: {dict}` line that printed the exports as a Python repr — unquoted
    # `None`/`True`, single-quoted keys — which no client could parse and which left
    # `verification` out of the content blocks altogether.
    parts.append(_json_block(response))
    # Kept as its own readable block even though the dump above repeats it: solver logs are
    # multi-line, and `\n`-escaped inside a JSON string they stop being readable.
    if response.get("stdout"):
        parts.append(_text(f"Stdout:\n{response['stdout']}"))
    execution_time = response.get("execution_time")
    if isinstance(execution_time, (int, float)) and not isinstance(execution_time, bool):
        parts.append(_text(f"Execution time: {execution_time:.3f}s"))

    return ToolResult(
        content=parts,
        structured_content=response,
    )
