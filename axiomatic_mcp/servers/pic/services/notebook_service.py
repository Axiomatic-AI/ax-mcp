import json
from typing import Any, Optional

import nbformat

from ....templates.analysis_cells_template import AnalysisCellsTemplate


class NotebookService:
    _instance: Optional["NotebookService"] = None

    def __init__(self) -> None:
        pass

    @classmethod
    def get_instance(cls) -> "NotebookService":
        if cls._instance is None:
            cls._instance = NotebookService()
        return cls._instance

    async def create_simulation_notebook(
        self,
        response: dict[str, Any],
        wavelengths: list[float],
    ) -> str:
        """
        Build a Jupyter notebook (nbformat JSON string) with simulation results.

        Args:
            response: Simulation response dict (from SimulationService).
            wavelengths: List of wavelengths used in the simulation.

        Returns:
            str: Notebook serialized as JSON
        """
        nb = nbformat.v4.new_notebook()

        # Core setup cells (data injection)
        setup_cells = [
            nbformat.v4.new_markdown_cell("# Photonic Circuit Simulation Results"),
            nbformat.v4.new_code_cell(
                f"wavelengths = {json.dumps(wavelengths, indent=2)}\nsimulation_data = {json.dumps(response, indent=2)}\nsimulation_data"
            ),
        ]

        # Inject analysis cells from the template
        analysis_cells = AnalysisCellsTemplate.get_cells()

        # Final notebook cells
        nb.cells = setup_cells + analysis_cells

        # Return notebook as serialized JSON string
        return nbformat.writes(nb)
