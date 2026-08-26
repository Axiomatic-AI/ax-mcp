"""Service for meep FDTD code generation and asynchronous job execution API calls."""

from typing import Any

import httpx

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase

# HTTP statuses the meep endpoints use to report something the caller can act on: a script
# that failed static validation (400), a key without playground access (403), an unknown
# task (404), results asked for too early (409), or a scheduler refusal (502). These are
# turned into result dicts so the tools can explain them; every other status stays an
# exception and surfaces as a ToolError.
_ACTIONABLE_STATUS_CODES = frozenset({400, 403, 404, 409, 502})

# No successful meep response body contains a "success" key (see api/src/models/meep.py),
# so its presence unambiguously marks one of the failure dicts built below. Callers must
# test `response.get("success") is False` — never truthiness, since it is None on success.
_FAILURE_MARKER = "success"


def _detail_dict(response: httpx.Response) -> dict[str, Any]:
    """Normalize a FastAPI error body into a dict.

    ``detail`` is a dict for the meep endpoints' own errors ({"error_type", "message", ...})
    but a bare string for framework errors — notably the 403 from is_playground_user_guard,
    which is just {"detail": "Not authorized"}.
    """
    try:
        body = response.json()
    except ValueError:
        return {"message": response.text.strip()}

    detail = body.get("detail") if isinstance(body, dict) else body
    if isinstance(detail, dict):
        return detail
    if detail is None:
        return {"message": response.text.strip()}
    return {"message": str(detail)}


def _http_failure(error: httpx.HTTPStatusError) -> dict[str, Any]:
    """Convert an actionable HTTP error into a failure dict the tools can present."""
    detail = _detail_dict(error.response)
    extra = {key: value for key, value in detail.items() if key not in ("message", "error_type")}
    return {
        _FAILURE_MARKER: False,
        "error": detail.get("message") or f"HTTP {error.response.status_code}",
        "error_type": detail.get("error_type") or "http_error",
        "status_code": error.response.status_code,
        **extra,
    }


class MeepService(SingletonBase):
    """Thin proxy service for the Axiomatic meep endpoints."""

    def write_code(
        self,
        problem_description: str,
        previous_code: str | None = None,
        previous_error: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate a meep FDTD script from a problem description.

        Returns:
            dict with keys: code, explanation, error, error_type
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.MEEP_WRITE_CODE,
                data={
                    "problem_description": problem_description,
                    "previous_code": previous_code,
                    "previous_error": previous_error,
                },
            )

    def execute_code(self, code: str) -> dict[str, Any]:
        """
        Submit a meep script as an asynchronous job.

        Returns:
            dict with keys: task_id, status, exports_detected, info — or a failure dict
            when the script was rejected by static validation or the caller lacks access.
        """
        try:
            with AxiomaticAPIClient() as client:
                return client.post(ApiRoutes.MEEP_EXECUTE, data={"code": code})
        except httpx.HTTPStatusError as e:
            if e.response.status_code in _ACTIONABLE_STATUS_CODES:
                return _http_failure(e)
            raise

    def get_status(self, task_id: str) -> dict[str, Any]:
        """
        Poll a meep job.

        Returns:
            dict with keys: task_id, status, error_trace — or a failure dict.
        """
        try:
            with AxiomaticAPIClient() as client:
                return client.get(ApiRoutes.MEEP_EXECUTE_STATUS.format(task_id=task_id))
        except httpx.HTTPStatusError as e:
            if e.response.status_code in _ACTIONABLE_STATUS_CODES:
                return _http_failure(e)
            raise

    def get_results(self, task_id: str) -> dict[str, Any]:
        """
        Fetch the exports of a completed meep job.

        Returns:
            dict with keys: task_id, console_output, exports, failed_objects — or a
            failure dict (409 while the job is still running).
        """
        try:
            with AxiomaticAPIClient() as client:
                return client.get(ApiRoutes.MEEP_EXECUTE_RESULTS.format(task_id=task_id))
        except httpx.HTTPStatusError as e:
            if e.response.status_code in _ACTIONABLE_STATUS_CODES:
                return _http_failure(e)
            raise
