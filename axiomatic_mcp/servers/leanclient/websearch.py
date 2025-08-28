import json
import os
import urllib.parse
import urllib.request

from mcp.server.fastmcp import Context

from .lean_client import setup_client_for_file, update_file
from .utils import format_line


def lean_leansearch_impl(ctx: Context, query: str, num_results: int = 5) -> list[dict] | str:
    """Search for Lean theorems, definitions, and tactics using leansearch.net."""
    try:
        headers = {"User-Agent": "lean-lsp-mcp/0.1", "Content-Type": "application/json"}
        payload = json.dumps({"num_results": str(num_results), "query": [query]}).encode("utf-8")

        req = urllib.request.Request(
            "https://leansearch.net/search",
            data=payload,
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            results = json.loads(response.read().decode("utf-8"))

        if not results or not results[0]:
            return "No results found."
        results = results[0][:num_results]
        results = [r["result"] for r in results]

        for result in results:
            result.pop("docstring", None)
            result["module_name"] = ".".join(result["module_name"])
            result["name"] = ".".join(result["name"])

        return results
    except Exception as e:
        return f"leansearch error:\n{e!s}"


def lean_loogle_impl(ctx: Context, query: str, num_results: int = 8) -> list[dict] | str:
    """Search for definitions and theorems using loogle."""
    try:
        req = urllib.request.Request(
            f"https://loogle.lean-lang.org/json?q={urllib.parse.quote(query)}",
            headers={"User-Agent": "lean-lsp-mcp/0.1"},
            method="GET",
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            results = json.loads(response.read().decode("utf-8"))

        if "hits" not in results:
            return "No results found."

        results = results["hits"][:num_results]
        for result in results:
            result.pop("doc", None)
        return results
    except Exception as e:
        return f"loogle error:\n{e!s}"


def lean_state_search_impl(ctx: Context, file_path: str, line: int, column: int, num_results: int = 5) -> list | str:
    """Search for theorems based on proof state using premise-search.com."""
    rel_path = setup_client_for_file(ctx, file_path)
    if not rel_path:
        return "Invalid Lean file path: Unable to start LSP server or load file"

    file_contents = update_file(ctx, rel_path)
    client = ctx.request_context.lifespan_context.client
    goal = client.get_goal(rel_path, line - 1, column - 1)

    f_line = format_line(file_contents, line, column)
    if not goal or not goal.get("goals"):
        return f"No goals found:\n{f_line}\nTry elsewhere?"

    goal = urllib.parse.quote(goal["goals"][0])

    try:
        url = os.getenv("LEAN_STATE_SEARCH_URL", "https://premise-search.com")
        req = urllib.request.Request(
            f"{url}/api/search?query={goal}&results={num_results}&rev=v4.17.0-rc1",
            headers={"User-Agent": "lean-lsp-mcp/0.1"},
            method="GET",
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            results = json.loads(response.read().decode("utf-8"))

        for result in results:
            result.pop("rev", None)
        # Very dirty type mix
        results.insert(0, f"Results for line:\n{f_line}")
        return results
    except Exception as e:
        return f"lean state search error:\n{e!s}"


def lean_hammer_premise_impl(ctx: Context, file_path: str, line: int, column: int, num_results: int = 32) -> list[str] | str:
    """Search for premises based on proof state using the lean hammer premise search."""
    rel_path = setup_client_for_file(ctx, file_path)
    if not rel_path:
        return "Invalid Lean file path: Unable to start LSP server or load file"

    file_contents = update_file(ctx, rel_path)
    client = ctx.request_context.lifespan_context.client
    goal = client.get_goal(rel_path, line - 1, column - 1)

    f_line = format_line(file_contents, line, column)
    if not goal or not goal.get("goals"):
        return f"No goals found:\n{f_line}\nTry elsewhere?"

    data = {
        "state": goal["goals"][0],
        "new_premises": [],
        "k": num_results,
    }

    try:
        url = os.getenv("LEAN_HAMMER_URL", "http://leanpremise.net")
        req = urllib.request.Request(
            url + "/retrieve",
            headers={
                "User-Agent": "lean-lsp-mcp/0.1",
                "Content-Type": "application/json",
            },
            method="POST",
            data=json.dumps(data).encode("utf-8"),
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            results = json.loads(response.read().decode("utf-8"))

        results = [result["name"] for result in results]
        results.insert(0, f"Results for line:\n{f_line}")
        return results
    except Exception as e:
        return f"lean hammer premise error:\n{e!s}"
