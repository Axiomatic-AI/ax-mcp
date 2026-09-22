import json
from typing import Any

import nbformat

from ....shared.models.singleton_base import SingletonBase
from ....templates.analysis_cells_template import AnalysisCellsTemplate


class NotebookService(SingletonBase):
    def create_simulation_notebook(
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

        setup_cells = [
            nbformat.v4.new_markdown_cell("# Photonic Circuit Simulation Results"),
            nbformat.v4.new_code_cell(
                f"wavelengths = {json.dumps(wavelengths, indent=2)}\nsimulation_data = {json.dumps(response, indent=2)}\nsimulation_data"
            ),
        ]

        analysis_cells = AnalysisCellsTemplate.get_cells()

        nb.cells = setup_cells + analysis_cells
        return nbformat.writes(nb)

    def get_analysis_notebook_content(self) -> str:
        """Builds a notebook containing only the analysis cells, without simulation values."""
        nb = nbformat.v4.new_notebook()
        nb.cells = AnalysisCellsTemplate.get_cells()
        return nbformat.writes(nb)
