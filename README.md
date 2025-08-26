# Axiomatic MCP Server

MCP (Model Context Protocol) server for the Axiomatic_AI platform, built with FastMCP in Python. Provides access to Axiomatic_AI's tools via MCP.

- **FastMCP-based server**: Built on the FastMCP framework for efficient MCP implementation
- **Axiomatic API integration**: Connects to Axiomatic AI's API for various tooling
- **Mathematical proof tools**: Includes Lean 4 theorem formalization and proof generation
- **Simple configuration**: Easy setup with API key environment variable

## Available Tools

The axiomatic_mcp package includes several domain-specific servers:

### Mathematical Proof Tools
- **Autoformalizer**: Translates natural language mathematical statements into Lean 4 theorem declarations
- **Lean Tools**: Provides access to Lean 4 theorem proving tools (search, diagnostics, file operations)
- **Prover**: Automatically generates proofs for Lean 4 theorems using AI assistance

### Content Processing Tools
- **PIC Domain**: Image processing and analysis tools
- **Documents**: Document processing and analysis tools
- **Statement Negation**: Tools for negating mathematical statements

## Installation

You can install each domain server independently based on your needs. These can be installed in many MCP clients such as Cursor or Claude.

### Mathematical Proof Tools Setup

**For Autoformalizer (Theorem Formalization):**

```json
{
  "axiomatic-autoformalizer": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-autoformalizer"],
    "env": {
      "ANTHROPIC_API_KEY": "your-anthropic-api-key-here"
    }
  }
}
```

**For Lean Tools (Lean 4 Integration):**

```json
{
  "axiomatic-lean-tools": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-lean-tools"],
    "env": {
      "ANTHROPIC_API_KEY": "your-anthropic-api-key-here"
    }
  }
}
```

**For Prover (Automated Proof Generation):**

```json
{
  "axiomatic-prover": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-prover"],
    "env": {
      "ANTHROPIC_API_KEY": "your-anthropic-api-key-here"
    }
  }
}
```

### Content Processing Tools Setup

**For PIC Domain:**

```json
{
  "axiomatic-pic": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-pic"],
    "env": {
      "AXIOMATIC_API_KEY": "your-axiomatic-api-key-here"
    }
  }
}
```

**For Documents:**

```json
{
  "axiomatic-documents": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-documents"],
    "env": {
      "AXIOMATIC_API_KEY": "your-axiomatic-api-key-here"
    }
  }
}
```

**For Statement Negation:**

```json
{
  "axiomatic-statement-negation": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-statement-negation"],
    "env": {
      "AXIOMATIC_API_KEY": "your-axiomatic-api-key-here"
    }
  }
}
```

### Complete Setup Example

For a complete mathematical proof workflow, you might want to install all three proof tools:

```json
{
  "mcpServers": {
    "axiomatic-autoformalizer": {
      "command": "uvx",
      "args": ["--from", "axiomatic-mcp", "axiomatic-autoformalizer"],
      "env": {
        "ANTHROPIC_API_KEY": "your-anthropic-api-key-here"
      }
    },
    "axiomatic-lean-tools": {
      "command": "uvx",
      "args": ["--from", "axiomatic-mcp", "axiomatic-lean-tools"],
      "env": {
        "ANTHROPIC_API_KEY": "your-anthropic-api-key-here"
      }
    },
    "axiomatic-prover": {
      "command": "uvx",
      "args": ["--from", "axiomatic-mcp", "axiomatic-prover"],
      "env": {
        "ANTHROPIC_API_KEY": "your-anthropic-api-key-here"
      }
    }
  }
}
```

## Development

1. Clone the repository:

```bash
git clone https://github.com/axiomatic/ax-mcp.git
cd ax-mcp
```

2. Install in development mode:

```bash
make install-dev
```

3. Add servers to Cursor using Python module paths:

### Mathematical Proof Tools (Development)

**For Autoformalizer:**

```json
{
  "axiomatic-autoformalizer": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.autoformalizer"],
    "env": {
      "ANTHROPIC_API_KEY": "your-anthropic-api-key-here"
    }
  }
}
```

**For Lean Tools:**

```json
{
  "axiomatic-lean-tools": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.lean_tools"],
    "env": {
      "ANTHROPIC_API_KEY": "your-anthropic-api-key-here"
    }
  }
}
```

**For Prover:**

```json
{
  "axiomatic-prover": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.prover"],
    "env": {
      "ANTHROPIC_API_KEY": "your-anthropic-api-key-here"
    }
  }
}
```

### Content Processing Tools (Development)

**For PIC Domain:**

```json
{
  "axiomatic-pic": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.pic"],
    "env": {
      "AXIOMATIC_API_KEY": "your-axiomatic-api-key-here"
    }
  }
}
```

**For Documents:**

```json
{
  "axiomatic-documents": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.documents"],
    "env": {
      "AXIOMATIC_API_KEY": "your-axiomatic-api-key-here"
    }
  }
}
```

**For Statement Negation:**

```json
{
  "axiomatic-statement-negation": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.statement_negation"],
    "env": {
      "AXIOMATIC_API_KEY": "your-axiomatic-api-key-here"
    }
  }
}
```

### Project Structure

```
ax-mcp/
├── axiomatic_mcp/
│   ├── shared/              # Shared utilities
│   └── servers/             # Domain-specific servers
│       ├── autoformalizer/  # Theorem formalization
│       ├── lean_tools/      # Lean 4 integration
│       ├── prover/          # Automated proof generation
│       ├── pic/             # Image processing
│       ├── documents/       # Document processing
│       └── statement_negation/ # Statement negation
├── proofs/                  # Lean 4 proof files
├── pyproject.toml           # Python package configuration
└── README.md
```

### Adding a New Server

1. Create server directory:

```bash
mkdir axiomatic_mcp/servers/my_domain
```

2. Create `__init__.py`:

```python
from .server import MyDomainServer

def main():
    server = MyDomainServer()
    server.run()
```

2. Create `__main__.py`:

```python
from . import main

if __name__ == "__main__":
    main()
```

3. Implement server in `server.py`:

```python
from fastmcp import FastMCP

mcp = FastMCP(
    name="NAME",
    instructions="""GIVE NICE INSTRUCTIONS""",
    version="0.0.1",
)

@mcp.tool(
    name="tool_name",
    description="DESCRIPTION",
    tags=["TAG"],
)
def my_tool():
  pass

# Add more tools as needed
```

4. Add entry point to `pyproject.toml`:

```toml
[project.scripts]
axiomatic-mydomain = "axiomatic_mcp.servers.my_domain:main"
```

## Usage Examples

### Mathematical Proof Workflow

1. **Formalize a theorem** using the Autoformalizer:
   ```
   "A set of 3x3 matrices whose entries are pure imaginary numbers forms a vector space over the real field R"
   ```

2. **Generate a proof** using the Prover:
   - The prover will automatically work through the proof step by step
   - Uses Lean 4 tools to verify each step
   - Produces a complete, verified proof

3. **Use Lean Tools** for:
   - Searching for existing theorems and lemmas
   - Checking proof diagnostics
   - Reading and writing Lean files
   - Running Lean code

### Content Processing Workflow

- **PIC Domain**: Process and analyze images
- **Documents**: Extract and process document content
- **Statement Negation**: Transform mathematical statements into their negations

## Troubleshooting

### Server not appearing in Cursor

1. Restart Cursor after updating MCP settings
2. Check the Output panel (View → Output → MCP) for errors
3. Verify the command path is correct

### Multiple servers overwhelming the LLM

Install only the domain servers you need. Each server runs independently, so you can add/remove them as needed.

### API connection errors

1. Verify your API key is set correctly
2. Check internet connection
3. Ensure you're using the correct API key type:
   - `ANTHROPIC_API_KEY` for mathematical proof tools
   - `AXIOMATIC_API_KEY` for content processing tools

### Lean 4 setup issues

1. Ensure Lean 4 is installed and accessible in your PATH
2. Check that the Lean project path is correctly configured
3. Verify that the `lake` command is available

## Release Process

### Publishing a Release

1. Create a new release branch
1. Update version in `pyproject.toml`
1. Commit and push changes
1. Create a pull request titled "Release: YOUR FEATURE(s)". Include detailed description of what's included in the release.
1. Create a GitHub release with tag `vX.Y.Z`
1. GitHub Actions automatically publishes to PyPI

The package is available at: https://pypi.org/project/axiomatic-mcp/
