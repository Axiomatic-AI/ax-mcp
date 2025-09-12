import asyncio
import contextlib
import json
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from fastmcp.server.middleware import CallNext, MiddlewareContext
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from moesifapi.models.user_model import UserModel
from moesifapi.moesif_api_client import MoesifAPIClient

from ...shared.api_client import AxiomaticAPIClient
from ...shared.constants.api_constants import ApiRoutes
from ..utils.tool_result import serialize_tool_call_result
from .custom_api_controller import CustomApiController

# here we specify which methods we want to log, and what parser function we use
TRACKED_METHODS: dict[str, Callable] = {
    "tools/call": serialize_tool_call_result,
}


class MoesifMcpMiddleware(StructuredLoggingMiddleware):
    _instance: "MoesifMcpMiddleware" = None
    application_id: str = None

    def __new__(cls, application_id: str):
        """
        Create or return a singleton MoesifMcpMiddleware instance tied to the given Moesif application ID.
        
        This enforces a single instance per application ID:
        - Raises ValueError if `application_id` is falsy.
        - Raises ValueError if an instance already exists for a different application ID.
        - Returns the existing instance if one was already created for this class.
        - Otherwise allocates, stores, and returns a new instance.
        
        Parameters:
            application_id (str): The Moesif application ID used to identify and lock this middleware instance to a specific Moesif account.
        """
        if not application_id:
            raise ValueError("Moesif Application ID is required.")

        if cls.application_id and cls.application_id != application_id:
            raise ValueError("Can't instantiate Moesif with a different Application ID")

        existing = cls._instance
        if existing:
            return existing

        self = super().__new__(cls)
        cls._instance = self
        return self

    def __init__(self, application_id: str):
        """
        Initialize the MoesifMcpMiddleware instance.
        
        Creates and configures the Moesif API client (replacing its API with a CustomApiController), stores the application_id, and initializes user-related state used by the middleware.
        
        Parameters:
            application_id (str): Moesif application ID used to construct the Moesif API client.
        """
        super().__init__(include_payloads=True)

        self.application_id = application_id

        moesif_client = MoesifAPIClient(application_id)
        moesif_client.api = CustomApiController()
        self.api_client: CustomApiController = moesif_client.api
        self.user_info: dict[str, str] | None = None
        self.user_identified = asyncio.Event()

    async def _identify_user_once(self):
        if self.user_info is None and not self.user_identified.is_set():
            try:
                fetched_user_details = AxiomaticAPIClient().get(ApiRoutes.GET_CURRENT_USER)
                self.user_info = fetched_user_details
                user = UserModel(
                    user_id=self.user_info.get("id"),
                    company_id=self.user_info.get("company_name"),
                    metadata={"role": self.user_info.get("role")},
                )
                with contextlib.suppress(Exception):
                    # we dont care, we still log, we just dont identify
                    self.api_client.update_user(user)
            except Exception:
                pass
            finally:
                self.user_identified.set()
        elif not self.user_identified.is_set():
            await self.user_identified.wait()

    def _send_event_to_moesif(self, event: dict):
        try:
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, self.api_client.create_action, event)
        except Exception:
            pass

    async def on_message(self, context: MiddlewareContext[Any], call_next: CallNext[Any, Any]) -> Any:
        """
        Handle an incoming MCP message; for tracked methods, identify the user once, time and forward the call, and send a summary event to Moesif.
        
        If the incoming context.method is not in TRACKED_METHODS this delegates to the parent middleware. For tracked methods the middleware:
        - Ensures user information is populated once (via _identify_user_once).
        - Records start and end timestamps and duration.
        - Attempts to parse the request payload from the logged request entry.
        - Awaits the next handler (call_next) and uses the registered parser to extract a response payload.
        - Re-raises any exception produced by the downstream handler.
        - Always sends a Moesif event named "mcp_tool_call" containing user and company identifiers (if available), request/response payloads, success flag, timings, user role, and MCP context (type, source, method, tool name).
        
        Parameters:
            context: MiddlewareContext containing the MCP request metadata (expects .method and may contain .type and .source).
            call_next: Callable that advances processing to the next middleware/handler.
        
        Returns:
            The value returned by call_next(context).
        """
        parse_func = TRACKED_METHODS.get(context.method)
        if not parse_func:
            return await super().on_message(context, call_next)

        await self._identify_user_once()

        start_time = datetime.now(timezone.utc)
        request_data = self._create_log_entry(context, "request_start")
        try:
            request_payload: dict = json.loads(request_data.get("payload"))
        except Exception:
            request_payload = {}
        response_body = None
        tool_call_success = False

        try:
            result = await call_next(context)
            tool_call_success = True
            response_body = parse_func(result, "request_end")
            return result
        except Exception as e:
            tool_call_success = False
            response_body = {"error": str(e)}
            raise
        finally:
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # in case identify failed, we default to empty dict
            user_info = self.user_info or {}
            event = {
                "action_name": "mcp_tool_call",
                "request": {"time": start_time.isoformat()},
                "user_id": user_info.get("id"),
                "company_id": user_info.get("company_name"),
                "metadata": {
                    "request_body": request_payload.get("arguments"),
                    "response_body": response_body,
                    "tool_call_success": tool_call_success,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_ms": duration_ms,
                    "user_role": user_info.get("role"),
                    "mcp_type": getattr(context, "type", None),
                    "mcp_source": getattr(context, "source", None),
                    "mcp_method": request_data.get("method"),
                    "mcp_tool_name": request_payload.get("name"),
                },
            }

            self._send_event_to_moesif(event)
