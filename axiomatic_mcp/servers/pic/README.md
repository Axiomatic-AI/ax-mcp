# AxPhotonicsPreview

An MCP server for designing, and simulating Photonic Integrated Circuits (PICs) using the Axiomatic AI platform.

## Overview

The AxPhotonicsPreview Server enables AI assistants to create photonic integrated circuit designs using natural language descriptions. It leverages the Axiomatic AI platform to generate GDSFactory-compatible Python code for photonic components and circuits, and provides tools to simulate them.

## Tools Available

### `design_circuit`

Designs a photonic integrated circuit based on natural language descriptions and optionally refines existing code.

**Parameters:**

- `query` (str, required): Natural language description of the desired photonic circuit
- `existing_code` (str, optional): Existing GDSFactory code to refine or build upon
- `output_path` (Path, optional): Path where the generated files (`circuit.py` and `statements.json`) will be stored. Defaults to the current working directory.
- `pdk_type` (str, optional): The pdk to be used by the tool to generate a circuit. If not provided, the user will be asked to chose from available ones.

**Outputs:**

1. **Python code (`circuit.py`)**  
   Procedural code using [gdsfactory](https://gdsfactory.github.io/gdsfactory/) to build and simulate the photonic integrated circuit.

2. **Statements (`statements.json`)**  
   A structured JSON file that formalizes the circuit description.

---

### `simulate_circuit`

Simulates a previously generated circuit and produces both the **wavelengths** used in the simulation and a **Jupyter Notebook** with the results.

**Parameters:**

- `file_path` (Path, required): Absolute path to the Python file (`circuit.py`) containing the circuit design.
- `statements_file_path` (Path, optional): Absolute path to a JSON statements file to define the wavelength range
- `wavelength_range` (tuple[float, float, int], optional): wavelength range (start, end, number of points) in um. Overridden by statements_file_path

**Outputs:**

- **Wavelengths**: A list of sampled wavelengths (default range around 1.25 μm ± 10%).
- **Jupyter Notebook (`*_simulation.ipynb`)**: Notebook containing the simulation results.
- **Structured Output**: Includes the notebook JSON and the wavelength list.

**Example Usage:**

```text
Simulate the circuit.py generated for a ring resonator
```

**Sample Output (structured):**

```json
{
  "notebook_path": "/path/to/circuit_simulation.ipynb",
  "notebook": "{... Jupyter notebook JSON ...}",
  "wavelengths": [1.125, 1.1275, 1.13, ..., 1.375]
}
```

---

### `list_available_pdks`

Gets a list of all available Process Design Kits (PDKs), with its granted status.

**Parameters:**

- This tool takes no parameters.

**Returns:**

- A list of existing PDKs, with name, description and granted status

**Example Usage:**

```
Give me a list of available PDKs
```

**Sample Output (structured):**

```json
{
  "pdks": [
    {
      "pdk_type": "cspdk.si220.cband",
      "description": "Cornerstone PDK on platform Si220 for C-band",
      "granted": true
    },
    {
      "pdk_type": "cspdk.si220.oband",
      "description": "Cornerstone PDK on platform Si220 for O-band",
      "granted": true
    },
    {
      "pdk_type": "amf.cband",
      "description": "AMF PDK for C-band",
      "granted": false
    },
    {
      "pdk_type": "amf.oband",
      "description": "AMF PDK for O-band",
      "granted": false
    }
  ]
}
```

---

### `get_pdk_info`

Gets detailed information about a specific PDK, including its available cross-sections, components, and circuit library.

**Parameters:**

- `pdk_type` (str, required): The name of the PDK to inspect (e.g., 'cspdk.si220.cband').

**Returns:**

- Detailed information for the specified PDK, including components and cross-sections.

**Example Usage:**

```
Give me more information about the cspdk.si220.cband PDK
```

## Features

- Natural language to GDSFactory code generation
- Structured statements in JSON format
- Circuit simulation with wavelength sweeps
- Circuit optimization from formalized constraints
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

## Installation

### System requirements

First, make sure that you have the AxPhotonicsPreview dependencies installed:

```bash
pip install "axiomatic-mcp[pic]"
```

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

See the [main README](https://github.com/Axiomatic-AI/ax-mcp#getting-an-api-key) for instructions on obtaining an API key.

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
