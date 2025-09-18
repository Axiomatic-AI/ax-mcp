import json
from typing import Annotated

from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..shared import AxiomaticAPIClient
from ..shared.constants.api_constants import ApiRoutes


async def internal_feedback(
    tool_name: Annotated[str, "The tool that was executed"],
    request: Annotated[dict, "The request sent to the tool"],
    response: Annotated[dict, "The response returned by the tool"],
    ctx=None,
) -> ToolResult:
    """Shared tool to send internal feedback for each LLM call using Axiomatic API."""

    prompt = f"""
    You are an evaluator for MCP tool interactions.

    Tool executed: {tool_name}
    Request: {json.dumps(request, indent=2, ensure_ascii=False)}
    Response: {json.dumps(response, indent=2, ensure_ascii=False)}

    Decide:
    - "value": one of [positive, negative, neutral]
    - "extra_note": 1–2 sentences explaining why

    Return valid JSON with keys: value, extra_note.
    """

    feedback_eval = {"value": "neutral", "extra_note": "Could not evaluate"}
    try:
        if ctx and hasattr(ctx, "llm"):
            raw_eval = await ctx.llm.complete(prompt)
            feedback_eval = json.loads(raw_eval)
    except Exception as e:
        feedback_eval = {"value": "neutral", "extra_note": f"LLM eval failed: {e}"}

    payload = {
        "value": feedback_eval["value"],
        "tool": tool_name,
        "query": request.get("query") if isinstance(request, dict) else None,
        "response": str(response)[:500],
        "origin": "mcp-platform",
        "extra_note": feedback_eval["extra_note"],
    }

    try:
        client = AxiomaticAPIClient()
        api_result = client.post(ApiRoutes.MCP_MODEL_FEEDBACK, json=payload)
    except Exception as e:
        return ToolResult(
            content=[TextContent(type="text", text=f"Failed to log feedback: {e}")],
            structured_content={"error": str(e), "payload": payload},
        )

    return ToolResult(
        content=[TextContent(type="text", text=f"Feedback logged for tool {tool_name}")],
        structured_content={"payload": payload, "api_result": api_result},
    )
