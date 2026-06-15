"""Service for equation derivation and checking API calls."""

from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class EquationsService(SingletonBase):
    """Thin proxy service for the equations derive and check endpoints."""

    def _build_files(
        self,
        task: str,
        markdown: str | None = None,
        pdf_file: tuple[str, bytes, str] | None = None,
    ) -> dict[str, Any]:
        """Assemble the multipart/form-data payload expected by the endpoints."""
        files: dict[str, Any] = {"task": (None, task)}
        if pdf_file is not None:
            files["pdf_file"] = pdf_file
        if markdown is not None:
            files["markdown"] = (None, markdown)
        return files

    def derive(
        self,
        task: str,
        *,
        markdown: str | None = None,
        pdf_file: tuple[str, bytes, str] | None = None,
    ) -> dict[str, Any]:
        """Derive an expression from markdown content or a PDF document.

        Returns:
            dict with keys: explanation, code
        """
        with AxiomaticAPIClient() as client:
            return client.post(ApiRoutes.EQUATIONS_DERIVE, files=self._build_files(task, markdown, pdf_file))

    def check(
        self,
        task: str,
        *,
        markdown: str | None = None,
        pdf_file: tuple[str, bytes, str] | None = None,
    ) -> dict[str, Any]:
        """Check the correctness of an equation from markdown content or a PDF document.

        Returns:
            dict with keys: explanation, code
        """
        with AxiomaticAPIClient() as client:
            return client.post(ApiRoutes.EQUATIONS_CHECK, files=self._build_files(task, markdown, pdf_file))
