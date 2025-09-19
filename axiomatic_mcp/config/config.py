from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class _BaseConfig(BaseSettings):
    model_config = SettingsConfigDict()


class _AppSettings(_BaseConfig):
    moesif_application_id: str | None = (
        "eyJhcHAiOiI0OTM6MjY5MSIsInZlciI6IjIuMSIsIm9yZyI6IjQyMDo2MzIiLCJwdWIiOnRydWUsImlhdCI6MTc1NjY4NDgwMH0."
        "DcpUTfu3KHdtySxt6VksTMVD5TQyd2AAsO9UGYqvF9s"
    )
    disable_telemetry: bool = Field(default=False, alias="DISABLE_TELEMETRY")


class _Settings(_BaseConfig):
    app: _AppSettings = _AppSettings()


@lru_cache
def get_settings():
    return _Settings()
