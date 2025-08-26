from typing import Optional


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
        # TODO: load from env, config file, or secrets manager
        return self._api_key

    def set_api_key(self, api_key: str) -> None:
        self._api_key = api_key
