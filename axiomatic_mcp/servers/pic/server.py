"""PIC (Photonic Integrated Circuit) domain MCP server."""

from typing import Annotated

import nbformat
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...shared import AxiomaticAPIClient
from .services.circuit_service import CircuitService
from .services.simulation_service import SimulationService
from .services.statements_service import StatementsService

mcp = FastMCP(
    name="Axiomatic PIC Designer",
    instructions="""This server provides tools to design, optimize,
    and simulate photonic integrated circuits.""",
    version="0.0.1",
)

circuit_service = CircuitService.get_instance()
statements_service = StatementsService.get_instance()
simulation_service = SimulationService.get_instance()


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
async def simulate_circuit(code: str, statements: list[dict]) -> dict:
    """
    Parameters:
        code: str - Python code (GDSFactory or similar) that defines the circuit
        statements: list[dict] - statements that may contain wavelength info

    Returns:
        dict with:
            - "notebook": nbformat JSON of the simulation results
            - "wavelengths": list of floats used in the simulation
    """
    # 1. Get netlist from user code
    netlist = await circuit_service.get_netlist_from_code(code)

    # 2. Extract wavelengths (or fallback to default)
    wavelengths = statements_service.extract_wavelengths_from_statements(statements)
    if wavelengths is None:
        base = 1.25
        delta = base * 0.1
        wavelengths = [round(base - delta + i * (2 * delta / 100), 6) for i in range(101)]

    # 3. Run simulation
    response = await simulation_service.simulate_from_code(
        {
            "netlist": netlist,
            "wavelengths": wavelengths,
        }
    )

    if not response:
        raise RuntimeError("Simulation service returned no response")

    # 4. Build a Jupyter Notebook with nbformat
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_markdown_cell("# Simulation Results"))
    nb.cells.append(nbformat.v4.new_code_cell("wavelengths = " + repr(wavelengths) + "\nresponse = " + repr(response) + "\nresponse"))

    return {
        "notebook": nbformat.writes(nb),
        "wavelengths": wavelengths,
    }
