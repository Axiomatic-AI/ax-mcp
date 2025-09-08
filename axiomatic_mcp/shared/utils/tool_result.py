from typing import Any

from fastmcp.tools.tool import ToolResult


def serialize_tool_call_result(result: ToolResult, event: str) -> dict[str, Any]:
    serializable_content = None
    if result.content is not None:
        serializable_content = [block.model_dump() for block in result.content]

    return {
        "content": serializable_content,
        "structured_content": result.structured_content,
        "event": event,
    }
