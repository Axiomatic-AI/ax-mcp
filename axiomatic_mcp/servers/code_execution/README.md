# Axiomatic Code Execution Server

An MCP server for executing Python code securely using the Axiomatic AI API.

## Overview

The Code Execution server enables AI assistants and developers to run Python code in a controlled environment. It supports execution with limited libraries such as `gdsfactory`, `z3`, and `json`, making it useful for photonic design workflows, symbolic reasoning, and structured data handling.

## Endpoint

### `POST /code-execution/python/execute`

**Description:**  
Execute Python code in a secure environment. Returns standard output or an error trace.

**Request Body (application/json):**

```json
{
  "code": "print('Hello, World!')"
}
```

**Response (200 – Successful):**

```json
{
  "output": "Hello, World!\n",
  "is_success": true,
  "error_trace": null
}
```

**Response (Error):**

```json
{
  "output": "",
  "is_success": false,
  "error_trace": "Traceback (most recent call last): ..."
}
```

**Supported Imports:**

- `gdsfactory`
- `z3`
- `json`

## Features

- Secure sandboxed Python execution
- Access to photonic design library (`gdsfactory`)
- Support for symbolic reasoning with `z3`
- Structured data manipulation with `json`
- Standard output and error trace capture

## Installation

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-code-execution&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4aW9tYXRpYy1jb2RlLWV4ZWN1dGlvbiIsImVudiI6eyJBWElPTUFUSUNfQVBJX0tFWSI6IkVOVEVSIFlPVVIgQVBJIEtFWSJ9fQ%3D%3D)

### Quick Install (via PyPI)

```json
{
  "axiomatic-code-execution": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-code-execution"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Development Install

```json
{
  "axiomatic-code-execution": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.code_execution"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

## Configuration

### Required Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)

See the [main README](../../../README.md#getting-an-api-key) for instructions on obtaining an API key.

## Best Practices

1. **Limit Scope**: Keep code snippets minimal and focused
2. **Use Supported Libraries**: Only `gdsfactory`, `z3`, and `json` are supported
3. **Validate Output**: Always check `is_success` and `error_trace`
4. **Avoid Heavy Computation**: Execution is designed for lightweight tasks

## Limitations

- Only selected libraries are available
- Long-running or resource-intensive code may be terminated
- File system and network access are restricted

## Support

For issues or questions:

- GitHub Issues: https://github.com/axiomatic/ax-mcp/issues
- Email: developers@axiomatic.ai
