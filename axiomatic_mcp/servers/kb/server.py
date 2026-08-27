"""AxKnowledgeBase MCP server — semantic search over Axiomatic's curated knowledge base."""

from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .services.knowledge_base_service import KnowledgeBaseService

mcp = FastMCP(
    name="AxKnowledgeBase Server",
    instructions="""This server provides access to Axiomatic's curated knowledge base:
    scientific papers, extracted entities (devices, materials, performance metrics), and
    passages retrieved via semantic search. Every result carries its source (paper id/title),
    so it should always be used and cited instead of relying on unsourced recollection of "standard
    results from the literature". Use search_knowledge_base for semantic/citation lookups,
    get_knowledge_base_schema to discover what entity and relationship types are available,
    get_knowledge_base_overview for corpus-level stats, and list_knowledge_base_papers to
    browse the paper corpus directly. Those four answer in prose; knowledge_graph_read is the
    tabular one — a read-only Cypher query returning entity nodes and their properties as rows,
    for when a passage will not do because the answer has to be a table (comparing entities
    across metrics, plotting, feeding a dataframe). Call get_knowledge_base_schema first to
    learn the labels and property names to query.
    """
    + get_feedback_prompt(
        [
            "search_knowledge_base",
            "get_knowledge_base_schema",
            "get_knowledge_base_overview",
            "list_knowledge_base_papers",
            "knowledge_graph_read",
        ]
    ),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)

knowledge_base_service = KnowledgeBaseService()


def _format_search_results(response: dict[str, Any]) -> str:
    results = response.get("results") or []
    if not results:
        return f"No knowledge base results found for query: {response.get('query', '')!r}"

    lines = [f"Found {response.get('count', len(results))} result(s):\n"]
    for i, result in enumerate(results, start=1):
        metadata = result.get("metadata") or {}
        source = metadata.get("paper_title") or metadata.get("paper_id") or "unknown source"
        lines.append(f"{i}. [source: {source}, score={result.get('score') or 0:.3f}]\n{result.get('text', '')}\n")
    return "\n".join(lines)


def _format_rows(response: dict[str, Any]) -> str:
    """Render the row envelope as a table. Rows are shown in full — the endpoint already
    caps them server-side and says so through `truncated`, and a second cap here would
    drop data silently."""
    rows = response.get("rows") or []
    if not rows:
        return "Query returned no rows."

    columns = response.get("columns") or list(rows[0].keys())
    widths = [max(len(str(col)), *(len(str(row.get(col, ""))) for row in rows)) for col in columns]
    lines = [
        " | ".join(str(col).ljust(w) for col, w in zip(columns, widths, strict=False)),
        "-+-".join("-" * w for w in widths),
    ]
    lines.extend(" | ".join(str(row.get(col, "")).ljust(w) for col, w in zip(columns, widths, strict=False)) for row in rows)
    lines.append(f"\n{response.get('count', len(rows))} row(s).")
    if response.get("truncated"):
        lines.append("Truncated at the server row limit — narrow the query to see the rest.")
    return "\n".join(lines)


@mcp.tool(
    name="search_knowledge_base",
    description=(
        "Semantic search over Axiomatic's curated knowledge base of scientific papers, entities "
        "(devices, materials, performance metrics), and prior results. Returns the most similar "
        "passages, each with its source (paper id/title) and similarity score, so results can be "
        "cited directly. Prefer this over unsourced claims like 'this is a standard result'."
    ),
    tags=["knowledge-base", "search", "citations"],
)
async def search_knowledge_base(
    query: Annotated[str, "Natural language question or topic to search for"],
    limit: Annotated[int, "Maximum number of passages to return (1-50)"] = 5,
) -> ToolResult:
    """Semantic search over the knowledge base."""
    try:
        response = knowledge_base_service.search(query, limit)
    except Exception as e:
        raise ToolError(f"Failed to search knowledge base: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_search_results(response))],
        structured_content=response,
    )


@mcp.tool(
    name="get_knowledge_base_schema",
    description=(
        "Retrieve the knowledge base schema: entity types with their properties, and "
        "relationship types with their properties and which entity types they connect. "
        "Useful for understanding what kinds of information the knowledge base holds."
    ),
    tags=["knowledge-base", "schema"],
)
async def get_knowledge_base_schema() -> ToolResult:
    """Retrieve the knowledge base schema."""
    try:
        response = knowledge_base_service.get_schema()
    except Exception as e:
        raise ToolError(f"Failed to retrieve knowledge base schema: {e!s}") from e

    nodes = response.get("nodes") or []
    relationships = response.get("relationships") or []
    lines = [f"Entity types ({len(nodes)}):"]
    for node in nodes:
        prop_names = ", ".join(p.get("name", "") for p in node.get("properties") or [])
        lines.append(f"  - {node.get('name')}: {prop_names or '(no properties)'}")
    lines.append(f"\nRelationship types ({len(relationships)}):")
    for rel in relationships:
        patterns = ", ".join(f"{p.get('from_label')}->{p.get('to_label')}" for p in rel.get("patterns") or [])
        lines.append(f"  - {rel.get('name')}: {patterns or '(no patterns)'}")

    return ToolResult(
        content=[TextContent(type="text", text="\n".join(lines))],
        structured_content=response,
    )


@mcp.tool(
    name="get_knowledge_base_overview",
    description=(
        "Retrieve corpus-level statistics for the knowledge base: total papers, total "
        "extracted key metrics, and the most common devices and materials. Useful for "
        "answering 'what's in the knowledge base' or getting oriented before searching."
    ),
    tags=["knowledge-base", "overview"],
)
async def get_knowledge_base_overview() -> ToolResult:
    """Retrieve knowledge base summary statistics."""
    try:
        response = knowledge_base_service.get_overview()
    except Exception as e:
        raise ToolError(f"Failed to retrieve knowledge base overview: {e!s}") from e

    devices = response.get("devices") or []
    materials = response.get("materials") or []
    lines = [
        f"Total papers: {response.get('total_papers', 0)}",
        f"Total extracted key metrics: {response.get('total_key_metrics', 0)}",
        "",
        f"Top devices ({len(devices)}):",
        *(f"  - {d.get('name')}: {d.get('count')}" for d in devices[:10]),
        "",
        f"Top materials ({len(materials)}):",
        *(f"  - {m.get('name')}: {m.get('count')}" for m in materials[:10]),
    ]

    return ToolResult(
        content=[TextContent(type="text", text="\n".join(lines))],
        structured_content=response,
    )


@mcp.tool(
    name="list_knowledge_base_papers",
    description=(
        "Browse papers ingested into the knowledge base, paginated. Returns each paper's "
        "id, title, authors, and how many extracted key metrics reference it. Use this to "
        "enumerate the corpus directly instead of semantic search, e.g. when the user asks "
        "'what papers do you have' or wants to page through the full list."
    ),
    tags=["knowledge-base", "papers", "browse"],
)
async def list_knowledge_base_papers(
    page: Annotated[int, "Page number, starting at 1"] = 1,
    page_size: Annotated[int, "Number of papers per page (1-100)"] = 20,
) -> ToolResult:
    """List papers in the knowledge base."""
    try:
        response = knowledge_base_service.list_papers(page, page_size)
    except Exception as e:
        raise ToolError(f"Failed to list knowledge base papers: {e!s}") from e

    items = response.get("items") or []
    if not items:
        return ToolResult(
            content=[TextContent(type="text", text=f"No papers found on page {page}.")],
            structured_content=response,
        )

    lines = [f"Page {response.get('page', page)} of {response.get('total_pages', 1)} ({response.get('total', 0)} papers total):\n"]
    for item in items:
        authors = ", ".join(item.get("authors") or []) or "unknown authors"
        lines.append(
            f"- {item.get('title', 'untitled')} ({item.get('paper_id', 'unknown id')}) "
            f"— {authors} — {item.get('keyMetricCount', 0)} key metric(s)"
        )

    return ToolResult(
        content=[TextContent(type="text", text="\n".join(lines))],
        structured_content=response,
    )


@mcp.tool(
    name="knowledge_graph_read",
    description=(
        "Execute a read-only Cypher query against the knowledge graph and return the rows. "
        "Use this when the answer has to be a table of entities and their properties — "
        "comparing devices across metrics, building a dataframe, plotting — rather than the "
        "prose passages search_knowledge_base returns. Only MATCH/RETURN is permitted. Call "
        "get_knowledge_base_schema first to learn the available labels and property names.\n\n"
        "Always alias individual properties in the RETURN clause; never return raw node or "
        "relationship objects (avoid `RETURN n`, write `RETURN n.name AS name`). For "
        "relationship queries, alias the source and target as `from` and `to` so the result "
        "renders as a graph."
    ),
    tags=["knowledge-base", "graph", "cypher"],
)
async def knowledge_graph_read(
    query: Annotated[str, "A read-only Cypher MATCH/RETURN query, aliasing specific properties"],
    params: Annotated[dict[str, Any] | None, "Optional query parameters, for safe value injection"] = None,
) -> ToolResult:
    """Read entity nodes and their properties out of the knowledge graph."""
    try:
        response = knowledge_base_service.execute_read(query, params)
    except Exception as e:
        raise ToolError(f"Failed to read the knowledge graph: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_rows(response))],
        structured_content=response,
    )
