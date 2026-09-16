import asyncio
from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class StatementsService(SingletonBase):
    async def validate_statements(self, query: dict[str, Any]) -> dict[str, Any]:
        """
        Call the VALIDATE_STATEMENTS API endpoint with a simulation request.
        query: {
            "netlist": ...,
            "statements": ...
        }
        """
        response = await asyncio.to_thread(
            AxiomaticAPIClient().post,
            ApiRoutes.VALIDATE_STATEMENTS,
            query,
        )

        if not response:
            raise RuntimeError("No response from validate_statements API")

        return response
