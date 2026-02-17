"""Service for argmin numerical optimization API calls."""

from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class ArgminService(SingletonBase):
    """Thin proxy service for argmin code generation and execution endpoints."""

    def generate_code(self, problem_description: str, problem_type: str) -> dict[str, Any]:
        """
        Generate Python code for a numerical problem.

        Args:
            problem_description: Natural language or mathematical description of the problem.
            problem_type: One of nonlinear_program, nonlinear_equations, initial_value_problem, optimal_control.

        Returns:
            dict with keys: code, explanation, error
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.ARGMIN_WRITE_CODE,
                data={
                    "problem_description": problem_description,
                    "problem_type": problem_type,
                },
            )

    def execute_code(self, code: str) -> dict[str, Any]:
        """
        Execute Python code in the argmin sandbox.

        Args:
            code: Python code to execute. Must call export(name, value).

        Returns:
            dict with keys: success, result, error, stdout, execution_time
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.ARGMIN_EXECUTE,
                data={"code": code},
            )
