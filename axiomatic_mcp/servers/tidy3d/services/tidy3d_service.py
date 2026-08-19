"""Service for Tidy3D FDTD/mode-solving code generation and execution API calls."""

from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class Tidy3DService(SingletonBase):
    """Thin proxy service for the Axiomatic Tidy3D endpoints."""

    def generate_code(
        self,
        problem_description: str,
        previous_code: str | None = None,
        previous_error: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate Python code for a Tidy3D simulation from a problem description.

        Returns:
            dict with keys: code, explanation, error
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.TIDY3D_GENERATE_CODE,
                data={
                    "problem_description": problem_description,
                    "previous_code": previous_code,
                    "previous_error": previous_error,
                },
            )

    def execute_code(self, code: str) -> dict[str, Any]:
        """
        Execute Tidy3D code. Local operations (e.g. the ModeSolver) run for free and
        return results synchronously. Code that calls submit_to_cloud(sim) uploads the
        simulation and returns a cost estimate WITHOUT starting the (paid) run.

        Returns:
            dict with keys: success, result, error, stdout, execution_time, task_id,
            task_status, estimated_cost_flex_credits, real_cost_flex_credits, error_type
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.TIDY3D_EXECUTE_CODE,
                data={"code": code},
            )

    def start_task(self, task_id: str, task_name: str | None = None) -> dict[str, Any]:
        """
        Start a previously estimated Tidy3D cloud task. This is the step that actually
        spends Flex credits — only call it after the estimated cost has been shown to
        and confirmed by the user.

        Returns:
            dict with keys: task_id, task_status
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.TIDY3D_START_TASK,
                data={"task_id": task_id, "task_name": task_name},
            )

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        Poll the status of a running/completed Tidy3D cloud task.

        Returns:
            dict with keys: task_id, task_status, real_cost_flex_credits
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.TIDY3D_TASK_STATUS,
                data={"task_id": task_id},
            )
