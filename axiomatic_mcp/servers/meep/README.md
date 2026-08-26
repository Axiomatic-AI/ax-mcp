# AxMeep Server

An MCP server that generates and runs [Meep](https://meep.readthedocs.io) FDTD electromagnetic simulations from natural language descriptions.

## Overview

Describe the simulation you want; the server writes a complete meep script, submits it as a remote job, and brings the results back. Meep needs conda + MPI, so simulations run as Kubernetes jobs rather than in-process: submission returns a `task_id` immediately, and you poll for completion. Results come back summarized — arrays as shape/dtype/min/max/mean, scalars exactly, figures as inline images — and every artifact is written to a local file you can load with numpy.

## Tools Available

### `generate_code`

Generate a meep script from a problem description. It only writes code; it never runs it. Say which results you want and under what names ("export the transmission spectrum as `transmission`") for better scripts.

**Parameters:**

- `problem_description` (str, required): geometry, materials, source, resolution, run time, and the results to export
- `previous_code` (str, optional): the script from a prior failed run
- `previous_error` (str, optional): that run's `error_trace`, so the generator patches the specific failure instead of starting over

### `execute_code`

Submit a script for execution. Returns a `task_id` immediately — **nothing has been simulated yet**. The script must `import meep` and contain at least one direct `export('name', obj)` call; otherwise it is rejected before submission at no cost. Typical runtime is 1–2 minutes (6 hour hard deadline).

### `get_simulation_status`

Check a job, optionally waiting for it.

**Parameters:**

- `task_id` (str, required)
- `wait_seconds` (int, optional, default `0`): seconds to wait, capped at 120 per call. Returns the moment the job is terminal, so a typical job needs one call. Do not loop with `wait_seconds=0`.

When the status is `failed`, feed the returned `error_trace` back into `generate_code` as `previous_error`.

### `get_results`

Fetch the exports of a completed job. Check the status first — calling early reports that the job is still running, it does not wait.

**Parameters:**

- `task_id` (str, required)
- `output_dir` (str, optional): where to write artifacts; a per-task subdirectory is created inside it. Defaults to `$AXIOMATIC_MEEP_OUTPUT_DIR`, else the working directory. An absolute path is recommended.
- `max_inline_images` (int, optional, default `4`): how many PNG figures to return inline

Pickled objects (`kind: pickle`) are saved but **never** deserialized — a meep pickle references the `meep` module and would not load without pymeep anyway. Prefer scripts that export arrays or figures, or print scalars to stdout.

**Example Usage:**

```
Simulate a 2D silicon waveguide bend at 1.55 um and show me the Ez field.
```

## Installation

### Quick Install (via PyPI)

```json
{
  "axiomatic-meep": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-meep"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Development Install

```json
{
  "axiomatic-meep": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.meep"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

## Configuration

### Required Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)

### Optional Environment Variables

- `AXIOMATIC_MEEP_OUTPUT_DIR`: base directory for downloaded artifacts (default: the working directory)

### Additional Requirements

- `execute_code`, `get_simulation_status` and `get_results` require an API key with **playground access** (ADMIN, INTERNAL or PLAYGROUND role), because each submission starts a Kubernetes pod. `generate_code` works with any authenticated key. Without the role those three tools report a clear authorization message.

## Limitations

- Simulations are asynchronous; there is no single call that submits and returns results.
- `wait_seconds` is capped at 120 s per call. If your MCP client's tool-execution timeout is shorter than the wait you ask for, the call can be cut short — Claude Code exposes `MCP_TOOL_TIMEOUT` (milliseconds) to raise it. The default `wait_seconds=0` never waits.
- Artifacts are capped by the backend at 50 MB each and 200 MB per job; oversized exports come back listed under failed objects. Downsample or slice inside the script.
- Exported pickles are not decoded here. Nothing in this package imports `dill`.
- Only numpy arrays (`.npy`/`.npz`) and matplotlib figures (PNG) come back readable. A **plain Python scalar**
  — a peak field value, an efficiency, a Q factor — is serialized as an opaque pickle, so ask for scalars to be
  printed as well as exported: printed values arrive in `console_output`. Wrapping the value in `np.asarray(...)`
  before exporting also works.
