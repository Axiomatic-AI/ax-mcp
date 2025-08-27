import os
from typing import Optional


# TODO: REMOVE THIS SERVICE
class ApiKeyService:
    _instance: Optional["ApiKeyService"] = None

    def __init__(self):
        self._api_key: str | None = None

    @classmethod
    def get_instance(cls) -> "ApiKeyService":
        if cls._instance is None:
            cls._instance = ApiKeyService()
        return cls._instance

    async def get_api_key(self) -> str | None:
        # TODO: Improve
        return os.getenv("AXIOMATIC_API_KEY")

    def set_api_key(self, api_key: str) -> None:
        self._api_key = api_key
