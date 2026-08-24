"""AxMeep MCP server — generate and run Meep FDTD simulations as asynchronous jobs."""

import asyncio
import time
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import ContentBlock, TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .artifacts import OUTPUT_DIR_ENV_VAR, excerpt_console, resolve_output_dir, summarize_exports
from .services.meep_service import MeepService

INSTRUCTIONS = """\
This server generates and runs Meep FDTD electromagnetic simulations.

WORKFLOW:
1. generate_code — turn a problem description into a complete, single-file meep script.
   It only writes code; it never runs it.
2. execute_code — submit that script. Meep runs as a remote Kubernetes job (conda + MPI),
   so this returns a task_id IMMEDIATELY and nothing has been simulated yet.
3. get_simulation_status(task_id, wait_seconds=120) — wait for the job. It returns the
   moment the job is terminal. Typical runtime is 1-2 minutes.
4. get_results(task_id) — fetch the exports once the status is 'completed'.

WAITING PROTOCOL: to wait, pass wait_seconds (cap 120 per call). Never loop bare
get_simulation_status() calls with wait_seconds=0 — that returns instantly and floods the
conversation. Chain at most ~5 waiting calls (~10 minutes total), then hand the task_id
back to the user and invite them to check later.

RETRY PROTOCOL: when a job reports status 'failed', feed its error_trace back into
generate_code as previous_error, together with the exact script you submitted as
previous_code. That patches the specific failure instead of starting over.

ACCESS: the three execute tools require an Axiomatic key with playground access
(ADMIN/INTERNAL/PLAYGROUND). generate_code works with any authenticated key. A 403 means
the key lacks the role — tell the user, do not retry.

RESULTS: a script returns values only via the export(name, obj) builtin, and must import
meep — both are checked statically before submission, at no cost. Exports come back
summarized (arrays as shape/dtype/min/max/mean), PNG figures are shown inline, and every
artifact is written to a local directory.

Only numpy arrays and matplotlib figures come back readable. A plain Python scalar (a
float such as a peak field value, an efficiency, a Q factor) is serialized as an opaque
pickle that this server will not decode, so ALWAYS ask for scalars to be printed as well
as exported — printed values arrive in console_output, which you can read. Either say so
in the problem_description ("print each scalar result"), or wrap the value in
np.asarray(...) before exporting it.
"""

mcp = FastMCP(
    name="AxMeep Server",
    instructions=INSTRUCTIONS + get_feedback_prompt(["generate_code", "execute_code", "get_simulation_status", "get_results"]),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)

meep_service = MeepService()

_MAX_WAIT_SECONDS = 120
_WAIT_POLL_INTERVAL_SECONDS = 5.0
_TERMINAL_STATUSES = ("completed", "failed")
_DEFAULT_MAX_INLINE_IMAGES = 4

PROBLEM_DESCRIPTION_ARG = Annotated[
    str,
    "Natural-language description of the simulation to build: geometry, materials, source, "
    "resolution, run time, and — importantly — which results to export and under what names "
    "(e.g. \"export the transmission spectrum as 'transmission'\").",
]
PREVIOUS_CODE_ARG = Annotated[
    str | None, "The exact script from a prior failed run, if retrying, so the generator can patch it instead of starting over."
]
PREVIOUS_ERROR_ARG = Annotated[str | None, "The error_trace reported by get_simulation_status for that failed run, if retrying."]
CODE_ARG = Annotated[
    str,
    "The meep Python script to run. Must import meep and contain at least one direct "
    "export('name', obj) call, or it is rejected before submission at no cost.",
]
TASK_ID_ARG = Annotated[str, "The task_id returned by execute_code."]
WAIT_SECONDS_ARG = Annotated[
    int,
    "Seconds to wait for the job to finish before answering, capped at 120 per call. "
    "Returns as soon as the job is terminal. 0 (the default) polls once and returns immediately.",
]
OUTPUT_DIR_ARG = Annotated[
    str | None,
    f"Directory to write artifacts into; a per-task subdirectory is created inside it. "
    f"Defaults to ${OUTPUT_DIR_ENV_VAR} if set, else the working directory. An absolute path is recommended.",
]
MAX_INLINE_IMAGES_ARG = Annotated[int, "How many PNG figures to return inline as images (the rest are written to disk and referenced by path)."]

# Output schemas deliberately declare NO "required" keys: every tool can answer with either
# its success shape or the service's {"success": false, ...} failure shape, and fastmcp
# validates structured_content against this schema client-side and raises on a mismatch.
# Undeclared fields pass through untouched, so future backend additions are safe.
_WRITE_CODE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": ["string", "null"], "description": "The generated meep script; pass it to execute_code."},
        "explanation": {"type": ["string", "null"]},
        "error": {"type": ["string", "null"]},
        "error_type": {"type": ["string", "null"], "description": "'generation_error' (retry once) or 'iteration_limit' (narrow the description)."},
    },
}
_EXECUTE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": ["string", "null"], "description": "Pass to get_simulation_status and get_results."},
        "status": {"type": ["string", "null"]},
        "exports_detected": {"type": "array", "items": {"type": "string"}},
        "info": {"type": ["string", "null"]},
        "success": {"type": "boolean", "description": "Present and false only when the submission was rejected."},
        "error": {"type": ["string", "null"]},
        "error_type": {"type": ["string", "null"]},
        "status_code": {"type": ["integer", "null"]},
    },
}
_STATUS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": ["string", "null"]},
        "status": {"type": ["string", "null"], "description": "queued | running | completed | failed."},
        "error_trace": {"type": ["string", "null"], "description": "Feed into generate_code as previous_error."},
        "waited_seconds": {"type": ["number", "null"]},
        "success": {"type": "boolean"},
        "error": {"type": ["string", "null"]},
        "error_type": {"type": ["string", "null"]},
        "status_code": {"type": ["integer", "null"]},
    },
}
_RESULTS_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": ["string", "null"]},
        "output_dir": {"type": ["string", "null"], "description": "Directory the artifacts were written to."},
        "console_output_path": {"type": ["string", "null"]},
        "console_output_excerpt": {"type": ["string", "null"]},
        "exports": {
            "type": "object",
            "description": "Per export: kind, size_bytes, path and a one-line summary. Never the raw payload.",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string"},
                    "size_bytes": {"type": "integer"},
                    "path": {"type": ["string", "null"]},
                    "summary": {"type": "string"},
                },
            },
        },
        "failed_objects": {"type": "object", "additionalProperties": {"type": "string"}},
        "success": {"type": "boolean"},
        "error": {"type": ["string", "null"]},
        "error_type": {"type": ["string", "null"]},
        "status_code": {"type": ["integer", "null"]},
    },
}

_ACCESS_DENIED_TEXT = (
    "Your Axiomatic API key does not have access to meep execution, which requires an ADMIN, INTERNAL or "
    "PLAYGROUND role. generate_code still works with any authenticated key. Tell the user their key needs "
    "playground access — do not retry."
)
_RETRY_GUIDANCE = {
    "generation_error": (
        " The generator run itself broke (model backend or timeout) — this is usually transient, so retrying this "
        "identical call once is worthwhile."
    ),
    "iteration_limit": (
        " The generator used up its self-correction attempts on this request. Do NOT resend the same description — "
        "narrow it, split the simulation, or name the exports explicitly."
    ),
}
_SCHEDULER_ERROR_SUFFIX = (
    "This is an infrastructure failure and says nothing about your script — report it to the user rather than "
    "rewriting the code. One exception: a malformed task_id also surfaces here (the scheduler looks ids up by "
    "UUID), so if you just passed one, check it came from execute_code."
)


def _text(message: str) -> TextContent:
    return TextContent(type="text", text=message)


def _is_failure(response: dict[str, Any]) -> bool:
    """A normalized service failure. `success` is absent (None) on every success path."""
    return response.get("success") is False


def _failure_text(response: dict[str, Any]) -> str:
    """Turn a normalized failure into guidance the caller can act on."""
    error_type = response.get("error_type")
    message = response.get("error") or "unknown error"
    status_code = response.get("status_code")

    if status_code == 403:
        return _ACCESS_DENIED_TEXT
    if error_type == "syntax_error":
        lineno = response.get("lineno")
        location = f" at line {lineno}" if lineno is not None else ""
        return (
            f"Submission rejected — the script is not valid Python{location}: {message}. Nothing was scheduled and "
            "nothing was charged. Fix it, or call generate_code with previous_code and this message as previous_error."
        )
    if error_type == "validation_error":
        return (
            f"Submission rejected: {message} Add a top-level `import meep as mp` (or `from meep import ...`) — a name "
            "that merely starts with 'meep' does not count. Nothing was scheduled."
        )
    if error_type == "no_exports":
        return (
            f"Submission rejected: {message} Add at least one direct `export('name', obj)` call — `mp.export(...)`, an "
            "aliased `e = export`, and `export()` inside a string or comment are all rejected. Nothing was scheduled."
        )
    if error_type == "task_not_found":
        return f"No meep job with that task_id: {message} Check the task_id returned by execute_code — job ids expire from the scheduler."
    if error_type == "not_completed":
        job_status = response.get("status") or "not finished"
        return (
            f"Results are not available yet — the job is '{job_status}'. Call get_simulation_status(task_id, wait_seconds=120) "
            "until it reports 'completed', then call get_results again."
        )
    if error_type == "scheduler_error":
        return f"The job scheduler refused the request: {message} {_SCHEDULER_ERROR_SUFFIX}"
    return f"Request failed: {message}"


@mcp.tool(
    name="generate_code",
    description=(
        "Generate a complete Meep FDTD simulation script from a natural-language problem description. "
        "Returns runnable Python and an explanation of the approach; it does NOT execute anything — run it "
        "with execute_code. The script imports meep and calls export(name, obj) for each result. If a run "
        "failed, pass previous_code and the error_trace as previous_error so the generator patches that "
        "specific failure instead of starting over. Naming the results you want in the description produces "
        "better scripts — and ask for any scalar results to be printed as well as exported, since a plain "
        "Python float comes back as an opaque pickle while printed values arrive in console_output."
    ),
    tags=["meep", "fdtd", "code-generation"],
    output_schema=_WRITE_CODE_OUTPUT_SCHEMA,
)
async def generate_code(
    problem_description: PROBLEM_DESCRIPTION_ARG,
    previous_code: PREVIOUS_CODE_ARG = None,
    previous_error: PREVIOUS_ERROR_ARG = None,
) -> ToolResult:
    """Generate a meep FDTD script from a problem description."""
    try:
        response = meep_service.write_code(problem_description, previous_code, previous_error)
    except Exception as e:
        raise ToolError(f"Failed to generate meep code: {e!s}") from e

    if response.get("error"):
        guidance = _RETRY_GUIDANCE.get(response.get("error_type") or "", "")
        return ToolResult(
            content=[_text(f"Code generation failed: {response['error']}{guidance}")],
            structured_content=response,
        )

    content: list[ContentBlock] = []
    explanation = response.get("explanation") or ""
    code = response.get("code") or ""
    if explanation:
        content.append(_text(explanation))
    if code:
        content.append(_text(f"```python\n{code}\n```"))
    content.append(_text("Next: run this with execute_code, then poll get_simulation_status(task_id, wait_seconds=120)."))

    return ToolResult(content=content, structured_content=response)


@mcp.tool(
    name="execute_code",
    description=(
        "Submit a Meep script for execution. Meep runs as a remote Kubernetes job (conda + MPI), so this "
        "returns a task_id immediately and nothing has been simulated yet — poll get_simulation_status, then "
        "call get_results. The script must import meep and contain at least one direct export('name', obj) "
        "call; otherwise it is rejected before submission at no cost. Typical runtime is 1-2 minutes (6 hour "
        "hard deadline). Requires a key with playground access."
    ),
    tags=["meep", "fdtd", "execution"],
    output_schema=_EXECUTE_OUTPUT_SCHEMA,
)
async def execute_code(code: CODE_ARG) -> ToolResult:
    """Submit a meep script as an asynchronous job."""
    try:
        response = meep_service.execute_code(code)
    except Exception as e:
        raise ToolError(f"Failed to submit meep job: {e!s}") from e

    if _is_failure(response):
        return ToolResult(content=[_text(_failure_text(response))], structured_content=response)

    task_id = response.get("task_id")
    parts = [_text(f"Submitted as task_id={task_id} (status: {response.get('status') or 'queued'}). Nothing has run yet.")]

    detected = response.get("exports_detected") or []
    if detected:
        parts.append(_text(f"Export names found by static analysis: {', '.join(detected)}"))
    info = response.get("info") or ""
    if info:
        parts.append(_text(info))
    parts.append(_text(f"Next: call get_simulation_status with task_id={task_id} and wait_seconds=120."))

    return ToolResult(content=parts, structured_content=response)


async def _poll_until_terminal(task_id: str, wait_seconds: int) -> tuple[dict[str, Any], float]:
    """Poll the status endpoint until the job is terminal or the (capped) budget runs out.

    The HTTP call goes through asyncio.to_thread and the pause through asyncio.sleep, so a
    120 s wait never blocks the event loop and the stdio transport stays responsive. This is
    safe because MeepService opens and closes a fresh httpx.Client per call — no client
    object is shared between threads.
    """
    budget = max(0, min(wait_seconds, _MAX_WAIT_SECONDS))
    started = time.monotonic()
    deadline = started + budget

    while True:
        try:
            response = await asyncio.to_thread(meep_service.get_status, task_id)
        except Exception as e:
            raise ToolError(f"Failed to get meep job status: {e!s}") from e

        now = time.monotonic()
        expired = now >= deadline
        if _is_failure(response):
            # A missing task will never appear and a 403 will never stop being one, so both
            # are surfaced immediately; a scheduler blip usually passes and the pod generally
            # keeps running through it, so only a persistent one is surfaced.
            if response.get("error_type") == "task_not_found" or response.get("status_code") == 403 or expired:
                return response, now - started
        elif response.get("status") in _TERMINAL_STATUSES or expired:
            return response, now - started

        await asyncio.sleep(min(_WAIT_POLL_INTERVAL_SECONDS, max(deadline - now, 0.0)))


@mcp.tool(
    name="get_simulation_status",
    description=(
        "Check a Meep job, optionally waiting for it to finish. Pass wait_seconds (capped at 120 per call) to "
        "wait — it returns the moment the job is terminal, so a typical 1-2 minute job needs one call. Do NOT "
        "loop with wait_seconds=0; chain at most ~5 waiting calls, then hand the task_id back to the user. "
        "When the status is 'failed', pass the returned error_trace to generate_code as previous_error."
    ),
    tags=["meep", "status"],
    output_schema=_STATUS_OUTPUT_SCHEMA,
)
async def get_simulation_status(task_id: TASK_ID_ARG, wait_seconds: WAIT_SECONDS_ARG = 0) -> ToolResult:
    """Poll a meep job, optionally long-polling until it is terminal."""
    response, waited = await _poll_until_terminal(task_id, wait_seconds)
    waited_text = f" after waiting {waited:.0f}s" if waited >= 1 else ""

    if _is_failure(response):
        return ToolResult(content=[_text(_failure_text(response))], structured_content={**response, "waited_seconds": waited})

    status = response.get("status")
    parts: list[ContentBlock] = []

    if status == "completed":
        parts.append(_text(f"Task {task_id} completed{waited_text}. Next: call get_results with this task_id."))
    elif status == "failed":
        parts.append(_text(f"Task {task_id} failed{waited_text}."))
        trace = response.get("error_trace")
        parts.append(_text(f"Error trace:\n{trace}" if trace else "The job reported no error trace."))
        parts.append(_text("To fix it, call generate_code with the exact script you submitted as previous_code and this trace as previous_error."))
    else:
        capped = f" The per-call cap is {_MAX_WAIT_SECONDS}s of the {wait_seconds}s requested." if wait_seconds > _MAX_WAIT_SECONDS else ""
        parts.append(_text(f"Task {task_id} is {status}{waited_text}.{capped}"))
        parts.append(
            _text(
                f"Call get_simulation_status again with wait_seconds={_MAX_WAIT_SECONDS} — do not loop with wait_seconds=0, that "
                "returns instantly. Chain at most ~5 waiting calls (~10 minutes), then hand the task_id back to the user."
            )
        )

    return ToolResult(content=parts, structured_content={**response, "waited_seconds": waited})


def _minimal_export_listing(exports: dict[str, Any]) -> list[str]:
    """Describe exports without touching the disk, for when artifacts cannot be written."""
    lines = []
    for name, artifact in exports.items():
        kind = artifact.get("kind") if isinstance(artifact, dict) else "unknown"
        size = artifact.get("size_bytes") if isinstance(artifact, dict) else None
        lines.append(f"{name} ({kind}, {size if size is not None else 'unknown'} bytes)")
    return lines


@mcp.tool(
    name="get_results",
    description=(
        "Fetch the exports of a completed Meep job. Check get_simulation_status first — calling this early "
        "reports that the job is still running, it does not wait. Each export is summarized (arrays as "
        "shape/dtype/min/max/mean, scalars exactly), PNG figures are returned inline as images, and every "
        "artifact is written to a local file whose path is returned so it can be loaded with numpy. Pickled "
        "objects are reported but never decoded."
    ),
    tags=["meep", "results", "artifacts"],
    output_schema=_RESULTS_OUTPUT_SCHEMA,
)
async def get_results(
    task_id: TASK_ID_ARG,
    output_dir: OUTPUT_DIR_ARG = None,
    max_inline_images: MAX_INLINE_IMAGES_ARG = _DEFAULT_MAX_INLINE_IMAGES,
) -> ToolResult:
    """Fetch, summarize and save the exports of a completed meep job."""
    try:
        response = meep_service.get_results(task_id)
    except Exception as e:
        raise ToolError(f"Failed to get meep results: {e!s}") from e

    if _is_failure(response):
        return ToolResult(content=[_text(_failure_text(response))], structured_content=response)

    exports = response.get("exports") or {}
    failed_objects = dict(response.get("failed_objects") or {})
    console_output = response.get("console_output") or ""

    try:
        directory = resolve_output_dir(task_id, output_dir)
        summaries = summarize_exports(exports, directory, max_inline_images)
        console_excerpt, console_path = excerpt_console(console_output, directory)
    except OSError as e:
        # Never lose a completed simulation's results to a disk problem.
        listing = _minimal_export_listing(exports)
        parts = [_text(f"Task {task_id} completed, but artifacts could NOT be written ({type(e).__name__}: {e}).")]
        if listing:
            parts.append(_text("Exports the job produced:\n" + "\n".join(listing)))
        if console_output:
            parts.append(_text(f"Console output (excerpt):\n{console_output[:2000]}"))
        return ToolResult(
            content=parts,
            structured_content={"task_id": task_id, "output_dir": None, "error": str(e), "failed_objects": failed_objects},
        )

    for summary in summaries:
        if summary.failure:
            failed_objects[summary.name] = summary.failure

    headline = f"Task {task_id} completed. {len(summaries)} export(s), {len(failed_objects)} failed. Artifacts written to {directory}"
    parts = [_text(headline)]
    for summary in summaries:
        parts.append(_text(summary.summary))
        if summary.image is not None:
            parts.append(summary.image)

    parts.append(_text(f"Console output:\n{console_excerpt}"))

    if failed_objects:
        parts.append(
            _text(
                "Exports that could not be returned:\n"
                + "\n".join(f"- {name}: {reason}" for name, reason in failed_objects.items())
                + "\nArtifacts are capped at 50 MB each and 200 MB per job — downsample, slice, or re-export at lower resolution in the script."
            )
        )
    elif not summaries:
        parts.append(
            _text(
                "The job completed but produced no exports. Its export() calls may sit in a branch that never ran — check the console output above."
            )
        )

    structured = {
        "task_id": response.get("task_id") or task_id,
        "output_dir": str(directory),
        "console_output_path": str(console_path) if console_path else None,
        "console_output_excerpt": console_excerpt,
        "exports": {
            s.name: {"kind": s.kind, "size_bytes": s.size_bytes, "path": str(s.path) if s.path else None, "summary": s.summary} for s in summaries
        },
        "failed_objects": failed_objects,
    }
    return ToolResult(content=parts, structured_content=structured)
