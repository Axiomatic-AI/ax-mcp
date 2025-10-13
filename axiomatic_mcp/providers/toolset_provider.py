from functools import lru_cache

from mcp import Tool

from ..shared.tools import internal_feedback_tool


@lru_cache
def get_mcp_tools() -> list[Tool]:
    try:
        return [internal_feedback_tool]
    except Exception:
        return []
