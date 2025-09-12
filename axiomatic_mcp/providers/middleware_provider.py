from fastmcp.server.middleware import Middleware

from ..config.config import get_settings
from ..shared.middleware.moesif_mcp_middleware import MoesifMcpMiddleware


def get_mcp_middleware() -> list[Middleware]:
    # This is our Publishable Application Id
    """
    Return a list of MCP middleware to apply for Moesif telemetry if enabled.
    
    If the application setting `moesif_application_id` is set and `disable_telemetry` is False, this returns a single-element list containing a configured MoesifMcpMiddleware. If middleware construction raises any exception, an empty list is returned. If telemetry is disabled or no application id is configured, the function returns None (no middleware provided).
    
    Returns:
        list[Middleware] | None: A list with the Moesif middleware when enabled, an empty list on instantiation failure, or None if telemetry is not enabled or no app id is configured.
    """
    app_settings = get_settings().app
    moesif_app_id = app_settings.moesif_application_id

    disable_telemetry = app_settings.disable_telemetry

    if moesif_app_id and not disable_telemetry:
        try:
            moesif_middleware = MoesifMcpMiddleware(application_id=moesif_app_id)
            return [moesif_middleware]
        except Exception:
            return []
