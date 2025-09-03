# Axiomatic PIC Designer Server

An MCP server for designing, optimizing, and simulating Photonic Integrated Circuits (PICs) using the Axiomatic AI platform.

## Overview

The PIC Designer server enables AI assistants to create photonic integrated circuit designs using natural language descriptions. It leverages the Axiomatic AI platform to generate GDSFactory-compatible Python code for photonic components and circuits, and provides tools to simulate them.

## Tools Available

### `design_circuit`

Designs a photonic integrated circuit based on natural language descriptions and optionally refines existing code.

**Parameters:**

- `query` (str, required): Natural language description of the desired photonic circuit
- `existing_code` (str, optional): Existing GDSFactory code to refine or build upon
- `output_path` (Path, optional): Path where the generated files (`circuit.py` and `statements.json`) will be stored. Defaults to the current working directory.

The `design_circuit` tool generates two outputs:

1. **Python code (`circuit.py`)**  
   Procedural code using [gdsfactory](https://gdsfactory.github.io/gdsfactory/) to build and simulate the photonic integrated circuit.

2. **Statements (`statements.json`)**  
   A structured JSON file that formalizes the circuit description.  
   It includes:
   - List of components used in the design.
   - Connections and hierarchy between components.
   - Parameters such as dimensions, wavelengths, and PDK references.

The statements are meant for MCP clients and LLM agents to consume directly, enabling downstream reasoning (e.g., optimization, verification, or natural-language explanations) without needing to parse the Python code.

---

### `simulate_circuit`

Simulates a previously generated circuit and produces both the **wavelengths** used in the simulation and a **Jupyter Notebook** with the results.

**Parameters:**

- `file_path` (Path, required): Absolute path to the Python file (`circuit.py`) containing the circuit design.

**Outputs:**

- **Wavelengths**: A list of sampled wavelengths (default range around 1.25 μm ± 10%).
- **Jupyter Notebook (`*_simulation.ipynb`)**: Notebook containing the simulation results, ready for visualization and further analysis.
- **Structured Output**: Includes the notebook JSON and the wavelength list for programmatic use.

**Example Usage:**

```text
Simulate the circuit.py generated for a ring resonator
```

This will produce:

- `circuit_simulation.ipynb` – Jupyter notebook with plots/results
- A list of wavelengths sampled for the simulation

**Sample Output (structured):**

```json
{
  "message": "Simulation notebook saved at /path/to/circuit_simulation.ipynb",
  "notebook": "{... Jupyter notebook JSON ...}",
  "wavelengths": [1.125, 1.1275, 1.13, ..., 1.375]
}
```

---

### `list_available_pdks`

Lists all available PDKs that the user has access to.

---

### `get_pdk_info`

Returns detailed information about a specific PDK, including cross sections, components, and circuit library.

---

## Features

- Natural language to GDSFactory code generation
- Structured statements in JSON format
- Circuit simulation with wavelength sweeps
- Automatic Jupyter Notebook creation with results
- Support for common photonic components (waveguides, couplers, resonators, etc.)
- Code refinement capabilities
- Integration with standard photonic design workflows

---

## Example Flow

1. **Design** a circuit with `design_circuit`
   - Generates `circuit.py` and `statements.json`.
2. **Simulate** the circuit with `simulate_circuit`
   - Produces sampled `wavelengths` and a Jupyter Notebook with results.
3. **Inspect** results locally in Jupyter Lab/Notebook.
4. **Iterate** with refinements using the `existing_code` parameter.

---

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

---

## Configuration

### Required Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)

See the [main README](../../../README.md#getting-an-api-key) for instructions on obtaining an API key.

---

## Best Practices

1. **Clear Descriptions**: Provide specific parameters (dimensions, materials, wavelengths)
2. **Iterative Refinement**: Use `existing_code` parameter to refine designs
3. **Component Libraries**: Leverage standard PDK components when available
4. **Design Rules**: Specify fabrication constraints in your queries

---

## Limitations

- Generated code requires GDSFactory installation for execution. See [documentation](https://gdsfactory.github.io/gdsfactory/)
- Design complexity limited by model training data
- Fabrication-specific rules must be validated separately
- Simulation requires additional tools (Lumerical, MEEP, etc.)

---

## Integration with Design Flow

1. **Design Generation**: Use the MCP server to create initial designs
2. **Local Execution**: Run generated code with GDSFactory
3. **Simulation**: Use `simulate_circuit` to generate wavelength sweeps and notebook results

---

## Support

For issues or questions:

- GitHub Issues: https://github.com/axiomatic/ax-mcp/issues
- Email: developers@axiomatic.ai

---

## Related Resources

- [GDSFactory Documentation](https://gdsfactory.github.io/gdsfactory/)
