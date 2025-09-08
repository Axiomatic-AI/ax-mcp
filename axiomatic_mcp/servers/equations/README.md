# AxEquationExplorer Server

An MCP server that provides equation composition and validation capabilities using the Axiomatic AI platform, with a focus on creating custom equations together with derivation recipes.

## Tools Available

### `find_functional_form`

Generates the desired equation from all the other equations in the source text (and necessary external knowledge) in the form of a Python file explaining the derivation steps.

**Parameters:**

- `document` (Path, required): Path to the PDF file to analyze
- `task` (str, required): Description of the expression of interest

**Returns:**

- A `*_code.py` file containing the composed expression in Python (Sympy-compatible)
- Includes derivation logic in the generated code
- Comments explaining the detials of the workflow and other relevant information.

**Features:**

- Maintains original mathematical notation and conventions
- Provides derivation recipe in code
- Provides the report on what has been done throughout the derivation process

**Example Usage:**

Please, visit `/examples/equations/find_functional_form/` folder to see the example.

### `check_equation`

Validates equations or corrects potential errors. Produces a corrected Python file if necessary.

**Parameters:**

- `document` (Path, required): Path to the PDF or Markdown file to analyze
- `task` (str, required): Task for equation checking (e.g., “check if E=mc² is correct”)

**Returns:**

- A `*_code.py` file containing the composed expression in Python (Sympy-compatible)
- Comments explaining the detials of the workflow and other relevant information.


**Example Usage:**

Please, visit `/examples/equations/check_equation/` folder to see the examples.

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

---

## Configuration

### Required Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)

See the [main README](https://github.com/Axiomatic-AI/ax-mcp#getting-an-api-key) for instructions on obtaining an API key.

---

## Use Cases

- **Research Paper Analysis**: Ask and obtain equations that are not explicitly written in the paper you are analyzing
- **Derivation**: The tool produces Python code (`*_code.py`) with a derivation recipe
- **Validation**: The tool checks if equations are wrong or incomplete

---

## Limitations

- Requires internet connection for API access
- Works with a single paper — multiple paper context will be added in future releases
- Processing time depends on document length and derivation complexity

---

## Support

For issues or questions:

- GitHub Issues: https://github.com/axiomatic/ax-mcp/issues
- Email: developers@axiomatic.ai
