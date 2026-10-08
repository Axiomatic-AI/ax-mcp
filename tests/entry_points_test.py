"""Tests for the console-script entry points declared in pyproject.toml."""

import importlib
from pathlib import Path
from unittest.mock import patch

import pytest
import tomllib
from fastmcp import FastMCP

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
CONSOLE_SCRIPTS = tomllib.loads(PYPROJECT.read_text())["project"]["scripts"]

# Module-level main() functions that are not console scripts but still start a server.
EXTRA_MAINS = {
    "modelfitter.server": "axiomatic_mcp.servers.modelfitter.server:main",
    "axmodelfitter.server": "axiomatic_mcp.servers.axmodelfitter.server:main",
}


def _resolve(target: str):
    module_name, func_name = target.split(":")
    return getattr(importlib.import_module(module_name), func_name)


@pytest.mark.parametrize("target", [*CONSOLE_SCRIPTS.values(), *EXTRA_MAINS.values()], ids=[*CONSOLE_SCRIPTS, *EXTRA_MAINS])
def test_entry_point_runs_stdio_without_the_fastmcp_banner(target):
    """The FastMCP banner checks PyPI for a newer fastmcp before the server answers ``initialize``.

    That is an outbound request on every launch and, on a network that silently drops it, a
    multi-second stall that is never cached. Our users can't act on a fastmcp upgrade notice, so
    every entry point must start the stdio server with the banner (and with it the check) off.
    """
    main = _resolve(target)

    with patch.object(FastMCP, "run") as run, patch("axiomatic_mcp.setup"):
        main()

    run.assert_called_once()
    assert run.call_args.kwargs == {"transport": "stdio", "show_banner": False}
