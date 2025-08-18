# Axiomatic MCP Servers

Domain-specific MCP (Model Context Protocol) servers for the Axiomatic platform, built with FastMCP in Python. Each domain server can be installed and configured independently to avoid overwhelming LLMs with unrelated tools.

## Architecture

- **Domain-based servers**: Each server focuses on a specific domain
- **Shared API client**: Common Axiomatic API integration
- **Modular installation**: Install only the domains you need
- **Independent configuration**: Each server can be configured separately

## Available Domain Servers

### 1. PIC Server (Photonic Integrated Circuits)
Design, simulate, and optimize photonic integrated circuits.

**Tools:**
- `design_pic` - Design a PIC from component specifications
- `get_component_library` - Browse available photonic components
- `simulate_pic` - Run simulations on designs
- `optimize_pic_design` - Optimize existing designs
- `create_pic_from_template` - Use predefined templates

### 2. Electronics Server
Design and analyze electronic circuits and PCBs.

**Tools:**
- `design_pcb` - Create PCB layouts
- `analyze_circuit` - Run circuit analysis (DC, AC, transient)

### 3. Quantum Server
Design and simulate quantum circuits.

**Tools:**
- `design_quantum_circuit` - Create quantum circuits
- `simulate_quantum` - Run quantum simulations

## Installation for Cursor

You can install each domain server independently based on your needs.

### Method 1: Install Individual Servers (Recommended)

1. Install the package with pip:
```bash
pip install axiomatic-mcp
```

2. Add the servers you need to Cursor's MCP settings:

**For PIC Domain:**
```json
{
  "axiomatic-pic": {
    "command": "axiomatic-pic",
    "args": [],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

**For Electronics Domain:**
```json
{
  "axiomatic-electronics": {
    "command": "axiomatic-electronics",
    "args": [],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

**For Quantum Domain:**
```json
{
  "axiomatic-quantum": {
    "command": "axiomatic-quantum",
    "args": [],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

**Or install all domains at once:**
```json
{
  "axiomatic-pic": {
    "command": "axiomatic-pic",
    "args": [],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  },
  "axiomatic-electronics": {
    "command": "axiomatic-electronics",
    "args": [],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  },
  "axiomatic-quantum": {
    "command": "axiomatic-quantum",
    "args": [],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Method 2: Using uvx (No Installation Required)

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

**For Electronics Domain:**
```json
{
  "axiomatic-electronics": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-electronics"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Method 3: Local Development

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
    "args": ["-m", "axiomatic_mcp.domains.pic"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

**For Electronics Domain:**
```json
{
  "axiomatic-electronics": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.domains.electronics"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

## Configuration

### Environment Variables

Each server can be configured via environment variables:

```bash
# API Configuration (shared)
AXIOMATIC_API_URL=https://api.axiomatic.ai
AXIOMATIC_API_KEY=your-api-key-here

# Logging
AXIOMATIC_LOG_LEVEL=info

# PIC Domain Specific
AXIOMATIC_DEFAULT_WAVELENGTH=1550.0
AXIOMATIC_DEFAULT_MATERIAL=silicon
```

### Configuration File

Create `~/.axiomatic/config.json` for persistent configuration:

```json
{
  "log_level": "info",
  "api_url": "https://api.axiomatic.ai",
  "api_key": "your-api-key-here",
  "default_wavelength": 1550.0,
  "default_material": "silicon"
}
```

### Per-Server Configuration

You can also configure each server independently by passing different environment variables:

```json
{
  "axiomatic-pic": {
    "command": "axiomatic-pic",
    "args": [],
    "env": {
      "AXIOMATIC_API_KEY": "pic-specific-key",
      "AXIOMATIC_LOG_LEVEL": "debug"
    }
  },
  "axiomatic-electronics": {
    "command": "axiomatic-electronics",
    "args": [],
    "env": {
      "AXIOMATIC_API_KEY": "electronics-specific-key",
      "AXIOMATIC_LOG_LEVEL": "info"
    }
  }
}
```

## Usage Examples

### PIC Domain

```
Design a photonic integrated circuit with:
- A grating coupler for input
- A 1x2 MMI splitter
- Two ring resonators
- Photodetectors for output
```

### Electronics Domain

```
Design a PCB with:
- STM32 microcontroller
- Power regulation circuit
- USB interface
- Debug headers
```

### Quantum Domain

```
Create a quantum circuit with:
- 3 qubits
- Hadamard gates
- CNOT gates
- Measure all qubits
```

## Development

### Project Structure

```
ax-mcp/
├── axiomatic_mcp/
│   ├── shared/              # Shared utilities
│   │   ├── api_client.py    # Axiomatic API client
│   │   ├── base_server.py   # Base server class
│   │   ├── config.py        # Configuration management
│   │   └── logger.py        # Logging utilities
│   └── domains/             # Domain-specific servers
│       ├── pic/             # Photonics domain
│       ├── electronics/     # Electronics domain
│       └── quantum/         # Quantum domain
├── pyproject.toml           # Python package configuration
├── config.example.json      # Example configuration
└── .env.example            # Example environment variables
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

## Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black axiomatic_mcp
ruff check axiomatic_mcp

# Type checking
mypy axiomatic_mcp
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
3. Enable debug logging: `AXIOMATIC_LOG_LEVEL=debug`

## Support

- GitHub Issues: https://github.com/axiomatic/ax-mcp/issues
- Documentation: https://docs.axiomatic.ai
- API Reference: https://api.axiomatic.ai/docs

## License

MIT License - See LICENSE file for details