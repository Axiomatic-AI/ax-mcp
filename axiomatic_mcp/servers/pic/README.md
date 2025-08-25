# Axiomatic PIC Designer Server

An MCP server for designing, optimizing, and simulating Photonic Integrated Circuits (PICs) using the Axiomatic AI platform.

## Overview

The PIC Designer server enables AI assistants to create photonic integrated circuit designs using natural language descriptions. It leverages the Axiomatic_AI platform to generate GDSFactory-compatible Python code for photonic components and circuits.

## Tools Available

### `design_circuit`

Designs a photonic integrated circuit based on natural language descriptions and optionally refines existing code.

**Parameters:**

- `query` (str, required): Natural language description of the desired photonic circuit
- `existing_code` (str, optional): Existing GDSFactory code to refine or build upon

**Returns:**

- Generated Python code for the photonic circuit
- Suggested file creation with the circuit design code

**Features:**

- Natural language to GDSFactory code generation
- Support for common photonic components (waveguides, couplers, resonators, etc.)
- Circuit optimization suggestions
- Code refinement capabilities
- Integration with standard photonic design workflows

**Example Usage:**

```
Design a ring resonator with a 10 micron radius coupled to a straight waveguide
```

## Installation

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-pic&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4aW9tYXRpYy1waWMiLCJlbnYiOnsiQVhJT01BVElDX0FQSV9LRVkiOiJFTlRFUiBZT1VSIEFQSSBLRVkifX0%3D)

### Quick Install (via PyPI)

Add to your MCP client configuration:

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

### Development Install

For development or local modifications:

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

## Configuration

### Required Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)

See the [main README](../../../README.md#getting-an-api-key) for instructions on obtaining an API key.

## Best Practices

1. **Clear Descriptions**: Provide specific parameters (dimensions, materials, wavelengths)
2. **Iterative Refinement**: Use existing_code parameter to refine designs
3. **Component Libraries**: Leverage standard PDK components when available
4. **Design Rules**: Specify fabrication constraints in your queries

## Limitations

- Generated code requires GDSFactory installation for execution. See [documentation](https://gdsfactory.github.io/gdsfactory/)
- Design complexity limited by model training data
- Fabrication-specific rules must be validated separately
- Simulation requires additional tools (Lumerical, MEEP, etc.)
  - **MCP tools for simulation coming soon**

## Integration with Design Flow

1. **Design Generation**: Use the MCP server to create initial designs
2. **Local Execution**: Run generated code with GDSFactory
3. **Simulation**: Export to simulation tools for verification
4. **Fabrication**: Generate GDSII files for foundry submission

## Support

For issues or questions:

- GitHub Issues: https://github.com/axiomatic/ax-mcp/issues
- Email: developers@axiomatic.ai

## Related Resources

- [GDSFactory Documentation](https://gdsfactory.github.io/gdsfactory/)
