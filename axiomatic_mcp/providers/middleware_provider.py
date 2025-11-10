from functools import lru_cache

from fastmcp.server.middleware import Middleware


@lru_cache
def get_mcp_middleware() -> list[Middleware]:
    return []
