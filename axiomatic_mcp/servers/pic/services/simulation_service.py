from typing import Any, Optional

from ....shared import AxiomaticAPIClient
from ...constants.api_constants import ApiRoutes


class SimulationService:
    _instance: Optional["SimulationService"] = None

    @classmethod
    def get_instance(cls) -> "SimulationService":
        if cls._instance is None:
            cls._instance = SimulationService()
        return cls._instance

    async def simulate_from_code(self, query: dict[str, Any]) -> dict[str, Any]:
        """
        Call the GET_SAX_SPECTRUM API endpoint with a simulation request.
        query: {
            "netlist": ...,
            "wavelengths": ...
        }
        """
        response = AxiomaticAPIClient().post(ApiRoutes.GET_SAX_SPECTRUM, data=query)

        if not response:
            raise RuntimeError("No response from get_sax_spectrum API")

        return response
