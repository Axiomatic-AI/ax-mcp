"""AxKnowledgeBase MCP server — Axiomatic's curated knowledge base, and the caller's private one."""

import asyncio
from pathlib import Path
from typing import Annotated, Any

import filetype
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
    instructions="""This server provides access to two separate knowledge graphs, and the first
    thing to get right is which one a question is about.

    The CURATED knowledge base is Axiomatic's own: scientific papers, extracted entities (devices,
    materials, performance metrics), and passages retrieved via semantic search. It is read-only.
    Reach it with search_knowledge_base for semantic/citation lookups, get_knowledge_base_overview
    for what the corpus holds, and knowledge_graph_read when the answer has to be a table.

    The PRIVATE knowledge graph is the caller's organization's own — only the papers it ingested
    itself. It is the only writable graph. Reach it with search_private_knowledge_base,
    get_private_knowledge_base_overview and private_knowledge_graph_read, and write to it with
    ingest_pdf_to_private_knowledge_base. Ingestion takes minutes and returns only when finished;
    re-sending the same PDF is safe and is reported as already present, so retrying after a timeout
    is correct. Because it holds the call open that long, it is a good candidate for delegating to a
    background or sub-agent if you have one, so the wait does not block other work. A paper ingested
    this way lands ONLY in the private graph — it will never turn up in
    search_knowledge_base, so do not read its absence there as a failed ingestion. If the account
    has no private graph these four refuse with a message saying so, and no retry will help.

    get_knowledge_base_schema describes BOTH graphs, since every graph shares one schema. Call it
    first to learn the labels and property names before writing any Cypher.

    Search results carry their source (paper id/title), so they should always be used and cited
    instead of relying on unsourced recollection of "standard results from the literature". The two
    Cypher tools are the tabular ones — use them when a passage will not do because the answer has
    to be a table (comparing entities across metrics, plotting, feeding a dataframe). Their rows
    carry only what the query asks for, so every query must also return the source paper it came
    from; never present graph values as sourced unless their provenance columns are in the result.
    Cypher is also how you browse a corpus paper by paper, e.g.
    MATCH (p:Document) RETURN p.id AS paper_id, p.title AS title ORDER BY p.title LIMIT 50.
    """
    + get_feedback_prompt(
        [
            "search_knowledge_base",
            "get_knowledge_base_schema",
            "get_knowledge_base_overview",
            "knowledge_graph_read",
            "ingest_pdf_to_private_knowledge_base",
            "search_private_knowledge_base",
            "get_private_knowledge_base_overview",
            "private_knowledge_graph_read",
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


_MAX_CELL_CHARS = 200
_MAX_TABLE_CHARS = 10_000


def _cell(value: Any) -> str:
    text = str(value)
    return text if len(text) <= _MAX_CELL_CHARS else text[:_MAX_CELL_CHARS] + "…"


def _format_rows(response: dict[str, Any]) -> str:
    """Render the row envelope as a table, bounded by a character budget.

    The endpoint caps rows server-side and reports that through `truncated`, but a row cap does
    not bound response size — a query selecting long text properties blows it up well inside the
    cap. So cells are elided and the table stops at the budget, both of them visibly. Neither
    touches the structured result, which still carries every row in full."""
    rows = response.get("rows") or []
    if not rows:
        return "Query returned no rows."

    columns = response.get("columns") or list(rows[0].keys())
    cells = [[_cell(row.get(col, "")) for col in columns] for row in rows]
    widths = [max(len(str(col)), *(len(cell_row[i]) for cell_row in cells)) for i, col in enumerate(columns)]
    lines = [
        " | ".join(str(col).ljust(w) for col, w in zip(columns, widths, strict=False)),
        "-+-".join("-" * w for w in widths),
    ]
    budget = _MAX_TABLE_CHARS
    for cell_row in cells:
        line = " | ".join(cell.ljust(w) for cell, w in zip(cell_row, widths, strict=False))
        budget -= len(line) + 1
        if budget < 0:
            break
        lines.append(line)
    shown = len(lines) - 2
    lines.append(f"\n{response.get('count', len(rows))} row(s).")
    if shown < len(rows):
        lines.append(
            f"Table stopped after {shown} row(s) at the response size budget; the rest are in the "
            "structured result only. Narrow the query or drop long text properties from the RETURN."
        )
    if not any("paper" in str(col).lower() or "doc" in str(col).lower() for col in columns):
        lines.append(
            "No provenance column in these rows — they are uncited. Re-run the query joining each "
            "entity to its source Paper and returning paper_id/title before presenting the values."
        )
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


def _format_overview(response: dict[str, Any]) -> str:
    """Render node counts per label."""
    items = response.get("items") or []
    total = response.get("total", 0)
    if not items:
        return f"The graph holds no labelled nodes ({total} node(s) total)."

    width = max(len(str(item.get("label", ""))) for item in items)
    lines = [f"{total} node(s) total, by label ({len(items)} label(s), largest first):"]
    lines += [f"  {str(item.get('label', '')).ljust(width)}  {item.get('count', 0)}" for item in items]
    lines.append("A node with several labels is counted once per label, so these counts do not sum to the total.")
    return "\n".join(lines)


@mcp.tool(
    name="get_knowledge_base_overview",
    description=(
        "Retrieve corpus-level statistics for Axiomatic's curated knowledge base: the total node "
        "count and the breakdown by entity label, largest first. Useful for answering \"what's in "
        'the knowledge base" or getting oriented before searching. This describes the curated '
        "corpus only — for the organization's private graph use get_private_knowledge_base_overview."
    ),
    tags=["knowledge-base", "overview"],
)
async def get_knowledge_base_overview() -> ToolResult:
    """Retrieve knowledge base summary statistics."""
    try:
        response = knowledge_base_service.get_overview()
    except Exception as e:
        raise ToolError(f"Failed to retrieve knowledge base overview: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_overview(response))],
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
        "renders as a graph.\n\n"
        "Rows carry no provenance of their own, so every query must also return the paper each "
        "row came from. Entity, Statement and Passage nodes all carry `doc_id`, so the source is "
        "one index seek away — no need to walk the HAS_PASSAGE/HAS_STATEMENT/HAS_ENTITY chain:\n"
        "  MATCH (e:Entity) WHERE e.name CONTAINS $term\n"
        "  MATCH (p:Document {id: e.doc_id})\n"
        "  RETURN e.name AS name, p.id AS paper_id, p.title AS title\n"
        "Values returned without a paper_id (or doc_id) column are uncited and must not be "
        "presented as sourced results.\n\n"
        "The whole result comes back in one response, so keep it small: return only the "
        "properties you need, add an explicit LIMIT (100 rows is usually plenty), and never "
        "select an `embedding_*` property or bulk `Passage.text` — long values are elided from "
        "the table, and the query is cheaper written narrowly than trimmed afterwards."
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


# --- Private graph ----------------------------------------------------------------------------

_PDF_CONTENT_TYPE = "application/pdf"


def _format_ingest(response: dict[str, Any]) -> str:
    paper_id = response.get("paper_id") or "unknown id"
    title = response.get("title") or "untitled"

    if response.get("already_present"):
        return (
            f"{title!r} ({paper_id}) was already in the private knowledge graph. Nothing was ingested and "
            "nothing was extracted, so the zero counts are the expected result here rather than a failed "
            "extraction — the paper is already queryable."
        )

    lines = [
        f"Ingested {title!r} into the private knowledge graph as {paper_id}.",
        f"  passages:   {response.get('passages', 0)}",
        f"  entities:   {response.get('entities', 0)}",
        f"  statements: {response.get('statements', 0)}",
    ]
    if not response.get("pdf_stored"):
        lines.append(
            "The source PDF did not finish uploading, so it cannot be downloaded again. The paper itself is "
            "queryable; sending the same file again completes the upload."
        )
    lines.append("Verify with search_private_knowledge_base — an ingested paper never appears in search_knowledge_base.")
    return "\n".join(lines)


@mcp.tool(
    name="ingest_pdf_to_private_knowledge_base",
    description=(
        "Ingest one local PDF into the organization's private knowledge graph. The PDF is converted to "
        "markdown, its statements and entities are extracted, and the source PDF is stored. This is the only "
        "tool that writes to a knowledge graph, and the private graph is the only graph it writes to — an "
        "ingested paper is reachable through search_private_knowledge_base and private_knowledge_graph_read, "
        "and never through search_knowledge_base.\n\n"
        "Synchronous and slow: it returns when ingestion has finished, which takes minutes for a full paper. "
        "Re-sending the same PDF is safe — it is reported as already present rather than ingested twice — so "
        "on a timeout or an unclear failure, retrying is the correct move."
    ),
    tags=["knowledge-base", "private", "ingest", "write"],
)
async def ingest_pdf_to_private_knowledge_base(
    file_path: Annotated[Path, "The absolute path to the PDF file to ingest"],
    title: Annotated[str, "Leave empty to use the PDF's first heading."] = "",
    paper_id: Annotated[str, "Leave empty to derive it from a hash of the converted markdown."] = "",
) -> ToolResult:
    """Ingest one PDF into the organization's private knowledge graph."""
    path = Path(file_path)
    if not path.is_file():
        raise ToolError(f"No such PDF file: {path}")

    pdf_bytes = await asyncio.to_thread(path.read_bytes)
    if not pdf_bytes:
        raise ToolError(f"The file is empty: {path}")
    guessed = filetype.guess(pdf_bytes)
    if guessed is None or guessed.mime != _PDF_CONTENT_TYPE:
        found = guessed.mime if guessed else "an unrecognized type"
        raise ToolError(f"Only PDFs can be ingested, but {path.name} is {found}.")

    try:
        # Choose to pass by `asyncio.to_thread` just for the ingest
        response = await asyncio.to_thread(knowledge_base_service.private_ingest, path.name, pdf_bytes, title, paper_id)
    except Exception as e:
        raise ToolError(f"Failed to ingest the PDF: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_ingest(response))],
        structured_content=response,
    )


@mcp.tool(
    name="search_private_knowledge_base",
    description=(
        "Semantic search over the organization's private knowledge base — the papers it has ingested "
        "itself, not Axiomatic's curated corpus. Returns the most similar passages, each with its source "
        "paper, so results can be cited. Use this to find anything ingested with "
        "ingest_pdf_to_private_knowledge_base; use search_knowledge_base for the curated corpus."
    ),
    tags=["knowledge-base", "private", "search", "citations"],
)
async def search_private_knowledge_base(
    query: Annotated[str, "Natural language question or topic to search for"],
    limit: Annotated[int, "Maximum number of passages to return (1-50)"] = 5,
) -> ToolResult:
    """Semantic search over the private knowledge base."""
    try:
        response = knowledge_base_service.private_search(query, limit)
    except Exception as e:
        raise ToolError(f"Failed to search the private knowledge base: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_search_results(response))],
        structured_content=response,
    )


@mcp.tool(
    name="get_private_knowledge_base_overview",
    description=(
        "Node counts per entity label in the organization's private knowledge graph, largest first, "
        "with the graph's total node count. Use it to see what the private graph holds — including "
        "whether it holds anything at all — before searching or querying it."
    ),
    tags=["knowledge-base", "private", "overview"],
)
async def get_private_knowledge_base_overview() -> ToolResult:
    """Node counts per label in the private knowledge graph."""
    try:
        response = knowledge_base_service.private_overview()
    except Exception as e:
        raise ToolError(f"Failed to retrieve the private knowledge base overview: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_overview(response))],
        structured_content=response,
    )


@mcp.tool(
    name="private_knowledge_graph_read",
    description=(
        "Execute a read-only Cypher query against the organization's private knowledge graph and return "
        "the rows. The private counterpart of knowledge_graph_read: same query rules, same result shape, "
        "different graph. Only MATCH/RETURN is permitted.\n\n"
        "get_knowledge_base_schema describes this graph too — every graph shares one schema — so call it "
        "first for the labels and property names, and follow the same rules knowledge_graph_read states: "
        "alias individual properties (`RETURN e.name AS name`, never a bare `RETURN e`), return the source "
        "paper on every query so the rows are citable, keep an explicit LIMIT on it, and never select an "
        "`embedding_*` property or bulk `Passage.text`."
    ),
    tags=["knowledge-base", "private", "graph", "cypher"],
)
async def private_knowledge_graph_read(
    query: Annotated[str, "A read-only Cypher MATCH/RETURN query, aliasing specific properties"],
    params: Annotated[dict[str, Any] | None, "Optional query parameters, for safe value injection"] = None,
) -> ToolResult:
    """Read entity nodes and their properties out of the private knowledge graph."""
    try:
        response = knowledge_base_service.private_execute_read(query, params)
    except Exception as e:
        raise ToolError(f"Failed to read the private knowledge graph: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_rows(response))],
        structured_content=response,
    )
