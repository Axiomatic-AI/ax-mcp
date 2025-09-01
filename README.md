# Axiomatic MCP Servers

MCP (Model Context Protocol) servers that provide AI assistants with access to the Axiomatic_AI Platform - a suite of advanced tools for scientific computing, document processing, and photonic circuit design.

## Available Servers

### 📄 [Documents Server](./axiomatic_mcp/servers/documents/)

Convert PDF documents to markdown with advanced OCR and layout understanding.

### 🖌️ [Equations Server](./axiomatic_mcp/servers/equations/)

Compose equation of your interest based on information in the scientific paper.

### 🔬 [PIC Designer Server](./axiomatic_mcp/servers/pic/)

Design photonic integrated circuits using natural language descriptions.

### 📊 [Plots Server](./axiomatic_mcp/servers/plots/)

Extract numerical data from plot images for analysis and reproduction.

### 🖥️ [Code Execution Server](./axiomatic_mcp/servers/code_execution/)

Execute Python code in a secure environment with support for selected libraries (`gdsfactory`, `z3`, `json`).  
Useful for photonic design workflows, symbolic reasoning, and structured data manipulation.

### ⚙️ [Digital Twin Optimizer Server](./axiomatic_mcp/servers/dt_optimizer/)

Optimize mathematical models and digital twins using advanced algorithms and experimental data fitting.

### 📝 [Annotations Server](./axiomatic_mcp/servers/annotations/)

Create intelligent annotations for PDF documents with contextual analysis, equation extraction, and parameter identification.

### 🔬 [Lean Client Server](./axiomatic_mcp/servers/leanclient/)

Interactive Lean 4 theorem prover integration for formal mathematics. Provides tools for proof development, goal inspection, theorem search, and code completion within Lean projects.


## Getting an API Key

All Axiomatic MCP servers require an API key:

1. Contact developers@axiomatic-ai.com to request access
2. Add the API key to your MCP client configuration as `AXIOMATIC_API_KEY`

## Installation

Installation instructions can be found for each specific server in their README.

### Setting up MCP Servers in AI Clients

#### Claude Desktop

1. Open Claude Desktop settings
2. Navigate to Developer → Edit MCP config
3. Add the server configuration(s) above
4. Restart Claude Desktop

#### Cursor

1. Open Cursor settings (Cmd/Ctrl + ,)
2. Search for "MCP"
3. Add the server configuration(s) to the MCP settings
4. Restart Cursor

#### Other MCP Clients

Refer to your client's documentation for MCP server configuration.

## Development

### Local Development Setup

1. Clone the repository:

```bash
git clone https://github.com/axiomatic/ax-mcp.git
cd ax-mcp
```

2. Install in development mode:

```bash
make install-dev
```

3. Configure your MCP client to use local Python modules:

> See specific MCP server README for specific installation instructions.

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

6. Don't forget to link to your server's README.md in the main project README.md

### Release Process

#### Publishing a Release

1. Create a new release branch
1. Update version in `pyproject.toml`
1. Commit and push changes
1. Create a pull request titled "Release: YOUR FEATURE(s)". Include detailed description of what's included in the release.
1. Create a GitHub release with tag `vX.Y.Z`
1. GitHub Actions automatically publishes to PyPI

The package is available at: https://pypi.org/project/axiomatic-mcp/

## Contributing

We welcome contributions! To add a new server or improve existing ones:

1. Fork the repository
2. Create a feature branch
3. Implement your changes following the existing patterns
4. Add documentation to your server directory
5. Submit a pull request

For detailed guidelines on adding new servers, see the [Development](#development) section.

## Debugging

### Attaching debugpy to an MCP server

1. In the directory where you cloned the repo, run `make install-dev` to install the required dependencies and create a python venv.
2. In your IDE, add the following configuration to the **/Users/{user_name}/.cursor/mcp.json** file, to enable debugpy listen to your local mcp code execution, e.g. axiomatic-documents MCP: debugging:

```json
{
  "mcpServers": {
    "axiomatic-documents-debug": {
      "command": "/Users/{user_name}/Work/Repos/ax-mcp/.venv/bin/python",
      "cwd": "/Users/{user_name}/Work/Repos/ax-mcp",
      "args": [
        "-m",
        "debugpy",
        "--listen",
        "127.0.0.1:5678", // Use unique port when adding more MCPs to debug
        "--wait-for-client",
        "-m",
        "axiomatic_mcp.servers.documents" // Path to your MCP
      ],
      "env": {
        "AXIOMATIC_API_KEY": "xxxx-xxxx-xxxx-xxxx-xxxx"
      }
    }
  }
}
```

3. Add the following block to the **ax-mcp/.vscode/launch.json**, use the same port as the MCP you would like to debug:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach to DocumentsFastMCP server",
      "type": "debugpy",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678 // Use matching port from mcp.json
      },
      "justMyCode": false
    }
  ]
}
```

4. In your IDE settings, enable the MCP you are debugging. NOTE: After enabling the tool it should be in a yellow "Loading tools" state, if not toggle the switch and if that does not work, make sure you have the right requirements installed.
   ![alt text](images/cursor-settings.png)

5. At last, while the tool is in the yellow "Loading tools" state, go to the "Run and Debug" tab on the left of your IDE and click "Start Debugging", the MCP tool in the IDE settings should now be green and list the available tools. Once this is running, you can use breakpoints in the server code and see the execution.

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

## Support

- **Issues**: [GitHub Issues](https://github.com/axiomatic/ax-mcp/issues)
- **Email**: developers@axiomatic-ai.com

## Creating >>Add to Cursor<< button:

Copy your MCP client configuration and paste it there:

https://docs.cursor.com/en/tools/developers#generate-install-link
