# AxTidy3D Server

An MCP server that generates and runs Tidy3D electromagnetic simulations (FDTD, mode solving) from natural language descriptions.

## Overview

Describe the simulation you want; the server generates executable code, then runs it. Local operations (e.g. the mode solver) execute for free and return results immediately. Cloud FDTD runs go through a cost-safe two-step flow: uploading and estimating cost first, and only spending Flex credits once you explicitly confirm.

## Tools Available

### `generate_code`

Generate Python simulation code from a problem description. Pass `previous_code`/`previous_error` to retry a failed attempt instead of starting over.

### `execute_code`

Run the generated code. Local operations return results synchronously. Code that uploads to the cloud returns a `task_id`, `task_status="estimated"`, and `estimated_cost_flex_credits` — **nothing is billed yet**.

### `start_simulation`

Starts a previously estimated cloud task. **This is the only step that spends real Flex credits** — only call it after the estimated cost has been shown to and confirmed by the user.

**Parameters:**

- `task_id` (str, required): the task id returned by `execute_code`
- `task_name` (str, optional): display name for the task

### `get_simulation_status`

Poll a running/completed cloud task and its real cost once known.

**Example Usage:**

```
Set up a 2D FDTD simulation of a slab waveguide and estimate the cost before running it.
```

## Installation

### Quick Install (via PyPI)

```json
{
  "axiomatic-tidy3d": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-tidy3d"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Development Install

```json
{
  "axiomatic-tidy3d": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.tidy3d"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

## Configuration

### Required Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)

### Additional Requirements

- Cloud simulation runs require a Tidy3D API key linked to your Axiomatic account (Settings → API Keys) before `start_simulation` will work. Local-only operations (e.g. the mode solver) do not require this.

## Limitations

- Cloud runs incur real Flex credit cost — always review `estimated_cost_flex_credits` from `execute_code` before calling `start_simulation`
