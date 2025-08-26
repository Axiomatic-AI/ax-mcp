import asyncio
import uuid
from typing import Any, Optional

import httpx

from .api_key_service import ApiKeyService


class AxiomaticApiClient:
    _instance: Optional["AxiomaticApiClient"] = None

    def __init__(self):
        self.api_key_service = ApiKeyService.get_instance()
        self.base_url = "https://api.axiomatic-ai.com"
        self._tasks: dict[str, asyncio.Task] = {}

    @classmethod
    def get_instance(cls) -> "AxiomaticApiClient":
        if cls._instance is None:
            cls._instance = AxiomaticApiClient()
        return cls._instance

    async def _make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Any | None:
        request_id = str(uuid.uuid4())
        api_key = await self.api_key_service.get_api_key()
        if not api_key:
            raise ValueError("API key not configured")

        headers = kwargs.pop("headers", {})
        headers = {
            "accept": "application/json",
            "X-API-Key": api_key,
            **headers,
        }

        async with httpx.AsyncClient() as client:
            task = asyncio.create_task(client.request(method, f"{self.base_url}{endpoint}", headers=headers, **kwargs))
            self._tasks[request_id] = task

            try:
                response = await task
                content_type = response.headers.get("content-type", "")
                body = response.json() if "application/json" in content_type else response.text
                if not response.is_success:
                    raise RuntimeError(f"API request failed ({response.status_code}): {response.reason_phrase}\n{body}")

                return body
            except asyncio.CancelledError:
                print("Request was aborted.")
                return None
            finally:
                self._tasks.pop(request_id, None)

    async def get(self, endpoint: str, **kwargs) -> Any | None:
        return await self._make_request(endpoint, method="GET", **kwargs)

    async def post(self, endpoint: str, body: Any, **kwargs) -> Any | None:
        headers = kwargs.pop("headers", {})
        headers["Content-Type"] = "application/json"
        return await self._make_request(endpoint, method="POST", json=body, headers=headers, **kwargs)

    def cancel_request(self, request_id: str) -> None:
        task = self._tasks.get(request_id)
        if task:
            task.cancel()
            self._tasks.pop(request_id, None)

    def cancel_all_requests(self) -> None:
        for task in list(self._tasks.values()):
            task.cancel()
        self._tasks.clear()
