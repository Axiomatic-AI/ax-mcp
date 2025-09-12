from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class SimulationService(SingletonBase):
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
