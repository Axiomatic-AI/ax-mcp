# AxModelFitterV2

An MCP server for fitting parametric models to data using the `ax_core.model_fitter` JAX library.

Describe your model and data in plain language — the server generates executable JAX fitting code, then runs it in a sandboxed environment and returns the fitted parameters and diagnostics.

## Quick Start

### Getting an API Key

[![Static Badge](https://img.shields.io/badge/Get%20your%20API%20key-6EB700?style=flat)](https://docs.google.com/forms/d/e/1FAIpQLSfScbqRpgx3ZzkCmfVjKs8YogWDshOZW9p-LVXrWzIXjcHKrQ/viewform)

### Installation (via PyPI)

Add to your MCP client configuration:

```json
{
  "axiomatic-modelfitterv2": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-modelfitter"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Development Install

```json
{
  "axiomatic-modelfitterv2": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.modelfitter"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)
- `AXIOMATIC_API_URL`: API base URL (optional, defaults to production)

## Tools

### `generate_code`

Generates executable Python fitting code from a natural language problem description. Returns an explanation and a code block ready to pass to `execute_code`.

**Arguments:**
- `problem_description`: Natural language description of the model and data to fit

### `execute_code`

Runs Python code in a sandboxed environment with JAX (`jnp`), diffrax, equinox, and `ax_core.model_fitter` available. Code must call `export(name, value)` to return results.

**Arguments:**
- `code`: Python code to execute

## Workflow

```
1. generate_code(problem_description)  →  explanation + code
2. (optionally review / edit the code)
3. execute_code(code)                  →  fitted parameters + diagnostics
```

## Examples

See [`examples/modelfitter/`](../../../examples/modelfitter/README.md) for worked examples covering:
- Exponential decay with uncertainty quantification
- Lotka-Volterra predator-prey ODE fit
- Ring resonator Lorentzian/Gaussian lineshape comparison
- Multi-model AIC/BIC selection

## Support

- GitHub Issues: [Axiomatic MCP Issues](https://github.com/Axiomatic-AI/ax-mcp/issues)
- Email: [developers@axiomatic-ai.com](mailto:developers@axiomatic-ai.com)
