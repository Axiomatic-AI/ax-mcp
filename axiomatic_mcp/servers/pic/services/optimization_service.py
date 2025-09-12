from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.models.singleton_base import SingletonBase
from ...constants.api_constants import ApiRoutes


class OptimizationService(SingletonBase):
    async def optimize_code(self, query: dict[str, Any]) -> dict[str, Any]:
        """
        Call the GET_OPTIMIZED_CODE API endpoint with optimization request.
        query: {
            "code": str,          # Python code (gdsfactory circuit)
            "statements": list    # Parsed statements from statements.json
        }
        """

        response = AxiomaticAPIClient().post(ApiRoutes.GET_OPTIMIZED_CODE, data=query)

        if not response:
            raise RuntimeError("No response from get_optimized_code API")

        return response
