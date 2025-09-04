from typing import Any, Optional

from ....shared import AxiomaticAPIClient
from ...constants.api_constants import ApiRoutes


class OptimizationService:
    _instance: Optional["OptimizationService"] = None

    @classmethod
    def get_instance(cls) -> "OptimizationService":
        if cls._instance is None:
            cls._instance = OptimizationService()
        return cls._instance

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
