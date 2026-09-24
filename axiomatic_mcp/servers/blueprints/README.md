# AxBlueprints Server

An MCP server that exposes Axiomatic's catalog of component blueprints — versioned contracts for device components such as an MMI, a Y-junction or a travelling-wave electrode — and lets an agent read each contract one section at a time.

## Overview

A blueprint is identified by an id of the form `<domain>/<name>`, e.g. `photonics/mmi`. Its contract is a structured manifest (ports, modes, parameters, budgets, dependencies) plus markdown sections covering its lifecycle state, range of validity, provenance, design decisions, evaluation and verification.

The typical flow is `list_blueprints` to see what exists, then `get_blueprint` for the one the task needs. The agent never sees how blueprints are stored; the contract is whatever these two tools return.

**Check the status.** Every blueprint carries a lifecycle status. Only `verified`, `canonical` and `published` mean it has been validated; `scaffolded` (and every other status) means it has not. Both tools flag unverified blueprints inline so they are not cited as validated results. At the time of writing, every blueprint in the catalog is `scaffolded`.

## Tools Available

### `list_blueprints`

The catalog: one line per blueprint with its id, status, version, component type, optical/electrical port counts and the sections available to `get_blueprint`.

**Parameters:**

- `domain` (str, optional): only blueprints of this domain, e.g. `photonics`
- `status` (str, optional): only blueprints with this lifecycle status, e.g. `scaffolded`

### `get_blueprint`

One blueprint's contract.

**Parameters:**

- `blueprint_id` (str, required): the id as returned by `list_blueprints`, e.g. `photonics/mmi`
- `sections` (list, optional): any of `manifest`, `readme`, `state`, `validity`, `source`, `decisions`, `eval`, `verification`. Omit it for `manifest` + `state`

The text response carries a summary of the manifest (ports, modes, parameters, properties, dependencies, verification date) and the full markdown of every requested section, and lists the sections that were not fetched. The complete manifest is in the structured result.

Contracts are large — the default response is around 6 KB, and every section of the largest blueprint together is around 50 KB — so request only the sections the task needs.

An unknown id fails with the list of ids that exist; a section the blueprint does not have fails with the list of sections it does have.

**Example Usage:**

```
Which photonics blueprints are there, and which of them are verified?
```

```
Read the photonics/mmi blueprint's validity range and design decisions before sizing the splitter.
```

## Installation

### Quick Install (via PyPI)

```json
{
  "axiomatic-blueprints": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-blueprints"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Development Install

```json
{
  "axiomatic-blueprints": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.blueprints"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

## Configuration

### Required Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)

## Limitations

- Read-only: blueprints are authored elsewhere and reach the API on deploy, so a newly written blueprint does not show up here until then
- No search by metric or platform: the catalog is filtered only by domain and status
