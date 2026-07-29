"""Service for equation derivation and checking API calls."""

import base64
from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class EquationsService(SingletonBase):
    """Thin proxy service for the expressions derive and check endpoints."""

    def _build_payload(
        self,
        task: str,
        markdown: str | None = None,
        pdf_bytes: bytes | None = None,
    ) -> dict[str, Any]:
        """Assemble the JSON body expected by the /expressions endpoints.

        Exactly one of markdown or pdf_bytes must be provided; PDFs are sent base64-encoded.
        """
        if (markdown is None) == (pdf_bytes is None):
            raise ValueError("Provide exactly one of 'markdown' or 'pdf_bytes'")

        payload: dict[str, Any] = {"task": task}
        if markdown is not None:
            payload["markdown"] = markdown
        else:
            payload["pdf_base64"] = base64.b64encode(pdf_bytes).decode("ascii")
        return payload

    def derive(
        self,
        task: str,
        *,
        markdown: str | None = None,
        pdf_bytes: bytes | None = None,
    ) -> dict[str, Any]:
        """Derive an expression from markdown content or a PDF document.

        Returns:
            dict with keys: code, explanation, status
        """
        payload = self._build_payload(task, markdown=markdown, pdf_bytes=pdf_bytes)
        with AxiomaticAPIClient() as client:
            return client.post(ApiRoutes.EQUATIONS_DERIVE, data=payload)

    def check(
        self,
        task: str,
        *,
        markdown: str | None = None,
        pdf_bytes: bytes | None = None,
    ) -> dict[str, Any]:
        """Check the correctness of an equation from markdown content or a PDF document.

        Returns:
            dict with keys: code, explanation, status, is_correct
        """
        payload = self._build_payload(task, markdown=markdown, pdf_bytes=pdf_bytes)
        with AxiomaticAPIClient() as client:
            return client.post(ApiRoutes.EQUATIONS_CHECK, data=payload)
