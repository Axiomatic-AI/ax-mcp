"""PIC (Photonic Integrated Circuit) domain MCP server."""

import asyncio
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...shared import AxiomaticAPIClient
from .services.circuit_service import CircuitService
from .services.notebook_service import NotebookService
from .services.simulation_service import SimulationService

mcp = FastMCP(
    name="Axiomatic PIC Designer",
    instructions="""This server provides tools to design, optimize,
    and simulate photonic integrated circuits.""",
    version="0.0.1",
)

circuit_service = CircuitService.get_instance()
simulation_service = SimulationService.get_instance()
notebook_service = NotebookService.get_instance()


@mcp.tool(
    name="design_circuit",
    description="Design a photonic integrated circuit and optionally create a Python file",
    tags=["design", "gfsfactory"],
)
async def design(
    query: Annotated[str, "The query to design the circuit"],
    existing_code: Annotated[str | None, "Existing code to use as a reference to refine"] = None,
) -> ToolResult:
    """Design a photonic integrated circuit."""
    data = {
        "query": query,
    }

    if existing_code:
        data["code"] = existing_code

    response = AxiomaticAPIClient().post("/pic/circuit/refine", data=data)
    code: str = response["code"]

    file_name = "circuit.py"

    return ToolResult(
        content=[TextContent(type="text", text=f"Generated photonic circuit design for: {file_name}\n\n```python\n{code}\n```")],
        structured_content={
            "suggestions": [
                {"type": "create_file", "path": file_name, "content": code, "description": f"Create {file_name} with the generated circuit design"}
            ]
        },
    )


@mcp.tool(
    name="simulate_circuit",
    description="Simulates a circuit from code and returns a Jupyter notebook with results",
)
async def simulate_circuit(
    file_path: Annotated[Path, "The absolute path to the python file to analyze"],
) -> dict:
    """
    Parameters:
        code: str - Python code (GDSFactory or similar) that defines the circuit
        statements: list[dict] - statements that may contain wavelength info

    Returns:
        dict with:
            - "notebook": nbformat JSON of the simulation results
            - "wavelengths": list of floats used in the simulation
    """
    # Get the code from the file_path
    if not file_path.exists():
        raise FileNotFoundError(f"Code not found: {file_path}")

    if file_path.suffix.lower() != ".py":
        raise ValueError("File must be a Python file")

    code = await asyncio.to_thread(file_path.read_bytes)
    netlist = await circuit_service.get_netlist_from_code(code)

    wavelengths = None
    if wavelengths is None:
        base = 1.25
        delta = base * 0.1
        wavelengths = [round(base - delta + i * (2 * delta / 100), 6) for i in range(101)]

    response = await simulation_service.simulate_from_code(
        {
            "netlist": netlist,
            "wavelengths": wavelengths,
        }
    )

    if not response:
        raise RuntimeError("Simulation service returned no response")

    notebook_json = await notebook_service.create_simulation_notebook(
        response=response,
        wavelengths=wavelengths,
    )

    # Save the notebook alongside the .py file
    notebook_path = file_path.parent / f"{file_path.stem}_simulation.ipynb"
    with notebook_path.open("w", encoding="utf-8") as f:
        f.write(notebook_json)

    return {
        "message": f"Simulation notebook saved at {notebook_path}",
        "notebook": notebook_json,
        "wavelengths": wavelengths,
    }
