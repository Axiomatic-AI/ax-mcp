"""Tests for the all-in-one aggregate server that mounts every domain server."""

import pytest
import pytest_asyncio
from fastmcp.client import Client

import axiomatic_mcp
from axiomatic_mcp.servers import servers


@pytest.fixture(scope="module")
def aggregate():
    """The aggregate server with every domain server mounted, as ``main()`` builds it."""
    axiomatic_mcp.setup()
    return axiomatic_mcp.axiomatic_mcp


@pytest_asyncio.fixture
async def aggregate_client(aggregate):
    async with Client(transport=aggregate) as client:
        yield client


@pytest.mark.asyncio
async def test_tool_titles_name_the_server_and_the_tool(aggregate_client):
    """Clients that show ``title`` (some drop untitled tools) must get "<server>: <tool title>".

    Without an explicit title FastMCP derives one from the namespaced name, which reads
    "Axtidy3D Start Simulation" and leaves the twelve ``*_report_feedback`` tools near-identical.
    """
    expected = {}
    for server in servers:
        async with Client(transport=server["server"]) as standalone:
            for tool in await standalone.list_tools():
                expected[f"{server['name']}_{tool.name}"] = f"{server['name']}: {tool.title}"

    titles = {tool.name: tool.title for tool in await aggregate_client.list_tools()}

    assert titles == expected
    assert len(set(titles.values())) == len(titles)


@pytest.mark.asyncio
async def test_standalone_servers_keep_their_own_titles(aggregate):
    """The aggregate's titles are layered on in ``setup()`` (the ``aggregate`` fixture runs it), and
    must not leak onto the child servers when they are run standalone."""
    for server in servers:
        async with Client(transport=server["server"]) as client:
            titles = {tool.name: tool.title for tool in await client.list_tools()}

        assert not [title for title in titles.values() if title.startswith(f"{server['name']}: ")], server["name"]
        if server["name"] == "AxTidy3D":
            assert titles["start_simulation"] == "Start Simulation"
