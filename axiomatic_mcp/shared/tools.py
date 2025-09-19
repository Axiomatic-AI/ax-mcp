from typing import Annotated

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..shared import AxiomaticAPIClient
from ..shared.constants.api_constants import ApiRoutes


async def internal_feedback(
    previous_called_tool_name: Annotated[str, "The name of the previous tool called"],
    previous_tool_parameters: Annotated[dict, "The parameters/arguments that were provided to the previous tool"],
    previous_tool_response: Annotated[dict, "The response that was returned by the previous tool"],
    feedback: Annotated[str | None, "A short summary of how well the tool call went, and any issues encountered."] = None,
    feedback_value: Annotated[str, 'One of ["positive", "negative", "neutral"] indicating how well the tool call went.'] = "neutral",
) -> ToolResult:
    """Shared tool to send internal feedback for each LLM call using Axiomatic API."""

    payload = {
        "value": feedback_value,
        "tool": previous_called_tool_name,
        "query": str(previous_tool_parameters.get("query", "")) if isinstance(previous_tool_parameters, dict) else "",
        "response": str(previous_tool_response)[:500],
        "origin": "mcp-platform",
        "extra_note": feedback,
    }

    try:
        client = AxiomaticAPIClient()
        api_result = client.post(ApiRoutes.MCP_MODEL_FEEDBACK, data=payload)
    except Exception as e:
        return ToolResult(
            content=[TextContent(type="text", text=f"Failed to log feedback: {e}")],
            structured_content={"error": str(e), "payload": payload},
        )

    return ToolResult(
        content=[TextContent(type="text", text=f"Feedback logged for tool {previous_called_tool_name}")],
        structured_content={"payload": payload, "api_result": api_result},
    )
