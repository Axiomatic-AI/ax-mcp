from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class _BaseConfig(BaseSettings):
    model_config = SettingsConfigDict()


class _Settings(_BaseConfig):
    app: _BaseConfig = _BaseConfig()


@lru_cache
def get_settings():
    return _Settings()
