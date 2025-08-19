# Axiomatic MCP Server

MCP (Model Context Protocol) server for the Axiomatic_AI platform, built with FastMCP in Python. Provides access to Axiomatic_AI's tools via MCP.

- **FastMCP-based server**: Built on the FastMCP framework for efficient MCP implementation
- **Axiomatic API integration**: Connects to Axiomatic AI's API for various tooling
- **Simple configuration**: Easy setup with API key environment variable

## Installation

> **Important**: Not yet released to PyPi. Follow the developer for instructions for now

You can install each domain server independently based on your needs. These can be installed in many MCP clients such as cursor or claude.

**For PIC Domain:**

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-pic&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4aW9tYXRpYy1waWMiLCJlbnYiOnsiQVhJT01BVElDX0FQSV9LRVkiOiJFTlRFUiBZT1VSIEFQSSBLRVkifX0%3D)

```json
{
  "axiomatic-pic": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-pic"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

**For Documents:**

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-documents&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4aW9tYXRpYy1kb2N1bWVudHMiLCJlbnYiOnsiQVhJT01BVElDX0FQSV9LRVkiOiJFTlRFUiBZT1VSIEFQSSBLRVkifX0%3D)

```json
{
  "axiomatic-documents": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-documents"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
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

**For PIC Domain:**

```json
{
  "axiomatic-pic": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.pic"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
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
      "AXIOMATIC_API_KEY": "your-api-key-here"
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
├── pyproject.toml           # Python package configuration
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

5. Update README.md with instructions on installing your server. You can generate the "Add to cursor" button [here](https://docs.cursor.com/en/tools/developers)

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

## Release Process

### Publishing a Release

1. Create a new release branch
1. Update version in `pyproject.toml`
1. Commit and push changes
1. Create a pull request titled "Release: YOUR FEATURE(s)". Include detailed description of what's included in the release.
1. Create a GitHub release with tag `vX.Y.Z`
1. GitHub Actions automatically publishes to PyPI

The package is available at: https://pypi.org/project/axiomatic-mcp/
