# AxEquationExplorer Server

An MCP server that provides equation composition and validation capabilities using the Axiomatic AI platform, with a focus on creating custom equations together with derivation recipes.

## Tools Available

### `function_finder`

Generates the desired equation from all the other equations in the source text together with a Python file explaining the derivation steps.

**Parameters:**

- `document` (Path, required): Path to the PDF file to analyze
- `task` (str, required): Description of the expression of interest

**Returns:**

- A `*_code.py` file containing the composed expression in Python (Sympy-compatible)
- Includes derivation logic in the generated code

**Features:**

- Uses the Axiomatic `/document/expression/compose/markdown` endpoint
- Employs `shared/documents/pdf_to_markdown.py` to preprocess the PDF into Markdown
- Maintains original mathematical notation and conventions
- Provides derivation recipe in code

**Example Usage:**

Input the following query:

> Express the total mechanical energy in terms of velocity v and height h using the function_finder tool

And create a markdown file `example.md` with this content:

```markdown
The kinetic energy of a particle of mass m moving with velocity v is given by:

$$ E_k = \frac{1}{2} m v^2 $$

The potential energy in a gravitational field is given by:

$$ E_p = m g h $$
```

Then a file `example_code.py` is created next to `example.md` or a `expression_code.py` in your user directory in case that the LLM interprets the content and not the file itself.```

---

### `equation_checker`

Validates equations or corrects potential errors. Produces a corrected Python file if necessary.

**Parameters:**

- `document` (Path, required): Path to the PDF or Markdown file to analyze
- `task` (str, required): Task for equation checking (e.g., “check if E=mc² is correct”)

**Returns:**

- Validation results and corrections in text output
- No file is created (corrections are shown inline)

**Features:**

- Uses the same Axiomatic endpoint (`/document/expression/compose/markdown`)
- Provides corrected equations in Python (Sympy-compatible)

**Example Usage:**

Input the following query:

> Check if the expression for kinetic energy is correct using the equation_checker tool

With the following markdown file:

```markdown
The kinetic energy of a particle is written as:

$$ E_k = m v^2 $$
```

The tool suggests that based on the equation checker tool's analysis, the kinetic energy expression in your `example.md` file is incorrect.

---

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

See the [main README](../../../README.md#getting-an-api-key) for instructions on obtaining an API key.

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
