# Axiomatic PIC Designer Server

An MCP server for designing, optimizing, and simulating Photonic Integrated Circuits (PICs) using the Axiomatic AI platform.

## Overview

The PIC Designer server enables AI assistants to create photonic integrated circuit designs using natural language descriptions. It leverages the Axiomatic AI platform to generate GDSFactory-compatible Python code for photonic components and circuits, and provides tools to simulate and optimize them.

## Tools Available

### `design_circuit`

Designs a photonic integrated circuit based on natural language descriptions and optionally refines existing code.

**Parameters:**

- `query` (str, required): Natural language description of the desired photonic circuit
- `existing_code` (str, optional): Existing GDSFactory code to refine or build upon
- `output_path` (Path, optional): Path where the generated files (`circuit.py` and `statements.json`) will be stored. Defaults to the current working directory.

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

### `optimize_circuit`

Optimizes a photonic circuit by refining the generated code using its formalized statements.

**Parameters:**

- `code_path` (Path, required): Path to the Python file containing the circuit code.
- `statements_path` (Path, required): Path to the JSON file containing the circuit statements.

**Outputs:**

- **Optimized Python code (`*_optimized.py`)**: Refined version of the input circuit code.
- **Structured Output**: Returns the optimized file path and the optimized code.

**Example Usage:**

Suppose you have the following circuit in `circuit.py`:

```python
import gdsfactory as gf
import cspdk.si220.cband

pdk = cspdk.si220.cband.get_pdk()
pdk.activate()

c = gf.Component()

# Add MZI component
mzi = c << pdk.get_component("mzi", delta_length=10, cross_section="strip")
mzi.move((-34.55, 2.14))
mzi.name = "mzi"

# Add ports
c.add_port("in0", port=mzi.ports["o1"])
c.add_port("in1", port=mzi.ports["o2"])
c.add_port("out0", port=mzi.ports["o3"])
c.add_port("out1", port=mzi.ports["o4"])

c
```

And the following `statements.json`:

```json
{
  "statements": [
    {
      "type": "PARAMETER_CONSTRAINT",
      "text": "The circuit has one input port named 'in0' (corresponding to 'o1') and one output port named 'out0' (corresponding to 'o2').",
      "formalization": {
        "code": "n_ports == 2",
        "default_tolerance": 0.05,
        "mapping": {
          "n_ports": {
            "name": "number_of_ports",
            "arguments": { "port_type": "all", "component": "netlist" }
          }
        }
      },
      "validation": null
    },
    {
      "type": "PARAMETER_CONSTRAINT",
      "text": "The circuit has exactly one input port.",
      "formalization": {
        "code": "n_ports_in == 1",
        "default_tolerance": 0.05,
        "mapping": {
          "n_ports_in": {
            "name": "number_of_ports",
            "arguments": { "port_type": "in", "component": "netlist" }
          }
        }
      },
      "validation": null
    }
  ]
}
```

Running `optimize_circuit` with these inputs will produce a new file:

- `circuit_optimized.py` – optimized code satisfying the given constraints.

**Sample Output (structured):**

```json
{
  "optimized_file_path": "/path/to/circuit_optimized.py",
  "optimized_code": "import gdsfactory as gf ..."
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
- Circuit optimization from formalized constraints
- Automatic Jupyter Notebook creation with results
- Support for common photonic components (waveguides, couplers, resonators, etc.)
- Code refinement capabilities
- Integration with standard photonic design workflows

---
