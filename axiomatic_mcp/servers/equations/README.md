# Axiomatic Equations Server

An MCP server that provides equation composition capabilities using the Axiomatic AI platform, with a focus on creating the custom equation together with the derivation recipe.

## Tools Available

### `compose_expression`

generates the desired equation from all the other equations in the source text together with a code explaining the derivation steps.

**Parameters:**

- `file_path` (Path, required): The absolute path to the PDF file to analyze
- `task` (str, required): explanation of the expression of interest

**Returns:**

- Expression object of the composed expression together with descriptions of all symbols
- Comments if necessary
- Sympy code explaining how the composition of the desired equation was done.

**Features:**

- Uses Derivation endpoint and Equation Processing endpoint
- Employs shared/documents/pdf_to_markdown.py function to preprocess the pdf to MD format
- Maintains original mathematical notation and conventions.
- Provides units 

**Example Usage:**

```
Provide the formula that expresses N as a function of momentum and temperature
```

(wait for response)

```
Use the composed epxression to visualize N in the report youre writing.
```

## Installation

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-equations&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4aW9tYXRpYy1lcXVhdGlvbnMiLCJlbnYiOnsiQVhJT01BVElDX0FQSV9LRVkiOiJ5b3VyLWFwaS1rZXktaGVyZSJ9fQ%3D%3D)


### Quick Install (via PyPI)

Add to your MCP client configuration:

```json
{
  "axiomatic-equations": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-equations"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Development Install

For development or local modifications:

```json
{
  "axiomatic-equations": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.equations"],
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

## Use Cases

- **Research Paper Analysis**: Ask and obtain equations that are not explicitly written in the paper you are analyzing
- **Derivation**: The output of the tool contains a derivation code that explains how the equation was derived

## Limitations

- Requires internet connection for API access
- Works with single paper - multiple paper context will be added in future releases
- Processing time depends on document and derivation complexity 


## Support

For issues or questions:

- GitHub Issues: https://github.com/axiomatic/ax-mcp/issues
- Email: developers@axiomatic.ai
