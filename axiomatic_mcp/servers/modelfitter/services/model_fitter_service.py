"""Service for model fitter code generation and execution API calls."""

from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase
from ..data_inlining import build_preamble, load_table


class ModelFitterService(SingletonBase):
    """Thin proxy service for model fitter code generation and execution endpoints."""

    def generate_code(self, problem_description: str) -> dict[str, Any]:
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.MODEL_FITTER_WRITE_CODE,
                data={"problem_description": problem_description},
            )

    def execute_code(
        self,
        code: str,
        data_file: str | None = None,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        if data_file is not None:
            code = build_preamble(load_table(data_file), columns) + "\n" + code
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.MODEL_FITTER_EXECUTE,
                data={"code": code},
            )
