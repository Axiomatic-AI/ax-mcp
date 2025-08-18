from fastmcp import FastMCP

from ..config.config import get_settings
from ..shared.middleware.moesif_mcp_middleware import MoesifMcpMiddleware


def add_moesif_middleware(mcp: FastMCP):
    # This is our Publishable Application Id
    app_settings = get_settings().app
    moesif_app_id = app_settings.moesif_application_id

    disable_telemetry = app_settings.disable_telemetry

    if moesif_app_id and not disable_telemetry:
        try:
            moesif_middleware = MoesifMcpMiddleware(application_id=moesif_app_id)
            mcp.add_middleware(moesif_middleware)
        except Exception:
            # Error starting moesif, user can continue regardless
            pass
