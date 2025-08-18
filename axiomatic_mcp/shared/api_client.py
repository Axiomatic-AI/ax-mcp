import os
from typing import Any

import httpx

API_URL = "https://api.axiomatic-ai.com"
TIMEOUT = 30.0


class AxiomaticAPIClient:
    def __init__(self):
        api_key = os.getenv("AXIOMATIC_API_KEY")
        if not api_key:
            raise ValueError("AXIOMATIC_API_KEY environment variable is not set")

        self.client = httpx.Client(
            base_url=API_URL,
            timeout=TIMEOUT,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": api_key,
            },
        )

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self.client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    def post(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self.client.post(endpoint, json=json)
        response.raise_for_status()
        return response.json()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
