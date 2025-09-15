from functools import lru_cache

from fastmcp.server.middleware import Middleware

from ..config.config import get_settings
from ..shared.middleware.moesif_mcp_middleware import MoesifMcpMiddleware


@lru_cache
def get_mcp_middleware() -> list[Middleware]:
    # This is our Publishable Application Id
    app_settings = get_settings().app
    moesif_app_id = app_settings.moesif_application_id

    disable_telemetry = app_settings.disable_telemetry

    if moesif_app_id and not disable_telemetry:
        try:
            moesif_middleware = MoesifMcpMiddleware(application_id=moesif_app_id)
            return [moesif_middleware]
        except Exception:
            return []
