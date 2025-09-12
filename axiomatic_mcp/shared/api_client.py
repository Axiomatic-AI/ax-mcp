import os
from typing import Any

import httpx

API_URL = "https://api.axiomatic-ai.com"

TIMEOUT = 1000


class AxiomaticAPIClient:
    def __init__(self):
        """
        Initialize the AxiomaticAPIClient.
        
        Reads the AXIOMATIC_API_KEY environment variable and raises ValueError if it's not set. Creates an httpx.Client configured with the module API_URL and TIMEOUT, and default headers including the API key (X-API-Key) and an origin identifier (X-origin: "mcp-client").
        """
        api_key = os.getenv("AXIOMATIC_API_KEY")
        if not api_key:
            raise ValueError("AXIOMATIC_API_KEY environment variable is not set")

        self.client = httpx.Client(
            base_url=API_URL,
            timeout=TIMEOUT,
            headers={
                "X-API-Key": api_key,
                "X-origin": "mcp-client",
            },
        )

    def _handle_raise_for_status(self, response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            try:
                error_body = response.text
                raise httpx.HTTPStatusError(f"{e!s} - Response: {error_body}", request=response.request, response=response) from e
            except Exception:
                raise

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self.client.get(endpoint, params=params)
        self._handle_raise_for_status(response)
        return response.json()

    def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if files:
            # When uploading files, use multipart/form-data
            response = self.client.post(endpoint, files=files, data=data, params=params)
        else:
            # For JSON data, use application/json
            response = self.client.post(endpoint, json=data, params=params)

        self._handle_raise_for_status(response)
        return response.json()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
