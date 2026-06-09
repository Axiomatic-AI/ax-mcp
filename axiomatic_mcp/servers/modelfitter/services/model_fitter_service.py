"""Service for model fitter code generation and execution API calls."""

from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class ModelFitterService(SingletonBase):
    """Thin proxy service for model fitter code generation and execution endpoints."""

    def generate_code(self, problem_description: str) -> dict[str, Any]:
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.MODEL_FITTER_WRITE_CODE,
                data={"problem_description": problem_description},
            )

    def execute_code(self, code: str) -> dict[str, Any]:
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.MODEL_FITTER_EXECUTE,
                data={"code": code},
            )
