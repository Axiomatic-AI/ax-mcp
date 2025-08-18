# Axiomatic MCP Server

MCP (Model Context Protocol) server for the Axiomatic_AI platform, built with FastMCP in Python. Provides access to Axiomatic_AI's tools via MCP.

- **FastMCP-based server**: Built on the FastMCP framework for efficient MCP implementation
- **Axiomatic API integration**: Connects to Axiomatic AI's API for various tooling
- **Simple configuration**: Easy setup with API key environment variable

## Installation for Cursor

You can install each domain server independently based on your needs.

### Usage

Use uvx to run servers without installing:

**For PIC Domain:**
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


## Development

1. Clone the repository:
```bash
git clone https://github.com/axiomatic/ax-mcp.git
cd ax-mcp
```

2. Install in development mode:
```bash
pip install -e .
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


## Development

### Project Structure

```
ax-mcp/
├── axiomatic_mcp/
│   ├── shared/              # Shared utilities
│   └── servers/             # Domain-specific servers
├── pyproject.toml           # Python package configuration
```

### Adding a New Domain

1. Create domain directory:
```bash
mkdir axiomatic_mcp/domains/my_domain
```

2. Create `__init__.py`:
```python
from .server import MyDomainServer

def main():
    server = MyDomainServer()
    server.run()
```

3. Implement server in `server.py`:
```python
from axiomatic_mcp.shared import BaseServer, BaseConfig

class MyDomainServer(BaseServer):
    def setup_tools(self):
        @self.mcp.tool()
        def my_tool(param: str) -> dict:
            return {"result": "success"}
```

4. Add entry point to `pyproject.toml`:
```toml
[project.scripts]
axiomatic-mydomain = "axiomatic_mcp.domains.my_domain:main"
```

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

1. Update version in `pyproject.toml`
2. Commit and push changes
3. Create a GitHub release with tag `vX.Y.Z`
4. GitHub Actions automatically publishes to PyPI

The package is available at: https://pypi.org/project/axiomatic-mcp/
