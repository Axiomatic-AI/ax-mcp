"""PIC (Photonic Integrated Circuit) domain MCP server."""

import asyncio
import json
from pathlib import Path
from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from .services.circuit_service import CircuitService
from .services.notebook_service import NotebookService
from .services.optimization_service import OptimizationService
from .services.pdk_service import PdkService
from .services.simulation_service import SimulationService
from .utils.pdk import flatten_pdks_response

mcp = FastMCP(
    name="Axiomatic PIC Designer",
    instructions="""This server provides tools to design, optimize,
    and simulate photonic integrated circuits.""",
    version="0.0.1",
)

circuit_service = CircuitService.get_instance()
simulation_service = SimulationService.get_instance()
notebook_service = NotebookService.get_instance()
pdk_service = PdkService.get_instance()
optimization_service = OptimizationService.get_instance()


@mcp.tool(
    name="design_circuit",
    description="Designs a photonic integrated circuit using python and gdsfactory. Saves the generated code and formalized statements as files.",
    tags=["design", "gfsfactory"],
)
async def design(
    ctx: Context,
    query: Annotated[str, "The query to design the circuit"],
    existing_code: Annotated[str | None, "Existing code to use as a reference to refine"] = None,
    output_path: Annotated[
        Path | None, "The path to save the circuit and statements files. If not provided, the files will be saved in the current working directory."
    ] = None,
    pdk_type: Annotated[Path | None, "The user's selected PDK. If none is passed, we will prompt the user for one."] = None,
) -> ToolResult:
    """Design a photonic integrated circuit."""
    if not pdk_type:
        try:
            pdk_types = pdk_service.list_pdks()
            flattened_pdks = flatten_pdks_response(pdk_types)
            pdk_type = await ctx.elicit(message="Please select a PDK to generate the circuit", response_type=flattened_pdks)
        except Exception:
            pdk_type = "cspdk.si220.cband"

    refine_body = {
        "query": query,
        "pdk_type": pdk_type,
    }

    if existing_code:
        refine_body["code"] = existing_code

    refine_response = circuit_service.generate_pic_circuit(refine_body)
    code: str = refine_response["code"]

    formalize_body = {
        "pdk": pdk_type,
        "query": query,
        "statements": [],
    }

    formalize_response = circuit_service.get_statements(formalize_body)

    file_path = output_path or Path.cwd()

    if not file_path.exists():
        file_path.mkdir(parents=True)

    circuit_file_path = file_path / "circuit.py"

    with Path.open(circuit_file_path, "w") as f:
        f.write(code)

    statements_file_path = file_path / "statements.json"

    with Path.open(statements_file_path, "w") as f:
        json.dump(formalize_response, f)

    return ToolResult(
        content=[TextContent(type="text", text=(f"Generated circuit at {circuit_file_path}, statements at {statements_file_path}"))],
        structured_content={
            "circuit_file_path": str(circuit_file_path),
            "code": code,
            "statements_file_path": str(statements_file_path),
            "statements": formalize_response,
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

    return ToolResult(
        content=[
            TextContent(
                type="text",
                text=f"Simulation completed. Notebook saved at {notebook_path}",
            )
        ],
        structured_content={
            "notebook_path": str(notebook_path),
            "notebook": notebook_json,
            "wavelengths": wavelengths,
        },
    )


@mcp.tool(
    name="list_available_pdks",
    description="Get a list of all available PDKs that the user has access to.",
    tags=["design", "pdk"],
)
async def list_pdks():
    all_pdks = pdk_service.list_pdks()
    return ToolResult(
        content=[TextContent(type="text", text="Listing available PDKs")],
        structured_content=all_pdks,
    )


@mcp.tool(
    name="get_pdk_info",
    description="Get detailed information about a specific PDK, including cross sections, components, and circuit library.",
    tags=["design", "pdk"],
)
async def get_pdk_info(
    pdk_type: Annotated[str, "The name of the PDK. This is either provided by the user, or provided by the list_available_pdks tool"],
):
    response = pdk_service.get_pdk_info(pdk_type)
    return ToolResult(
        content=[TextContent(type="text", text=f"Retrieved information for PDK: {pdk_type}")],
        structured_content=response,
    )


@mcp.tool(
    name="optimize_circuit",
    description="Optimizes a photonic circuit by refining the generated code using its statements.",
    tags=["optimize", "gfsfactory"],
)
async def optimize_circuit(
    code_path: Annotated[Path, "Path to the Python file containing the circuit code"],
    statements_path: Annotated[Path, "Path to the JSON file containing the circuit statements"],
) -> ToolResult:
    """Optimize a photonic integrated circuit."""
    if not code_path.exists():
        raise FileNotFoundError(f"Circuit code not found: {code_path}")
    if not statements_path.exists():
        raise FileNotFoundError(f"Statements file not found: {statements_path}")

    code = code_path.read_text(encoding="utf-8")
    with statements_path.open("r", encoding="utf-8") as f:
        statements_json = json.load(f)

    statements_list = statements_json.get("statements", [])
    request_body = {
        "code": code,
        "statements": statements_list,
    }
    response = await optimization_service.optimize_code(request_body)

    optimized_code = response.get("optimized_code", "")

    optimized_file_path = code_path.parent / f"{code_path.stem}_optimized.py"
    with optimized_file_path.open("w", encoding="utf-8") as f:
        f.write(optimized_code)

    return ToolResult(
        content=[
            TextContent(
                type="text",
                text=f"Optimized circuit saved at {optimized_file_path}",
            )
        ],
        structured_content={
            "optimized_file_path": str(optimized_file_path),
            "optimized_code": optimized_code,
        },
    )
