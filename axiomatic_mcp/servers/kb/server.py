"""AxKnowledgeBase MCP server — Axiomatic's curated knowledge base, and the caller's private one."""

import asyncio
import base64
from pathlib import Path
from typing import Annotated, Any, Literal

import filetype
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.shared.exceptions import McpError
from mcp.types import ClientCapabilities, ElicitationCapability, ImageContent, TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .services.knowledge_base_asset_service import KnowledgeBaseAssetService
from .services.knowledge_base_service import KnowledgeBaseService

mcp = FastMCP(
    name="AxKnowledgeBase Server",
    instructions="""This server provides access to two separate knowledge graphs, and the first
    thing to get right is which one a question is about.

    The CURATED knowledge base is Axiomatic's own: scientific papers, extracted entities (devices,
    materials, performance metrics), and passages retrieved via semantic search. It is read-only.
    Reach it with search_knowledge_base for semantic/citation lookups, get_knowledge_base_overview
    for what the corpus holds, knowledge_graph_read when the answer has to be a table,
    get_knowledge_base_paper_markdown to read one paper's full text, and
    search_paper_assets/get_paper_asset for its figures and tables — if a passage mentions "Figure
    4" or "Table 2", search that paper's assets for it rather than guessing at its content.

    The PRIVATE knowledge graph is the caller's organization's own — only the papers it ingested
    itself. It is the only writable graph. Reach it with search_private_knowledge_base,
    get_private_knowledge_base_overview, list_private_knowledge_base_papers,
    private_knowledge_graph_read, get_private_knowledge_base_paper_markdown and
    search_private_paper_assets/get_private_paper_asset, write to it with
    ingest_pdf_to_private_knowledge_base, and remove a paper from it with
    delete_private_knowledge_base_paper — every one of these except search/list/ingest takes the
    paper's id, which list_private_knowledge_base_papers and search_private_knowledge_base both
    report.
    Ingestion takes minutes and returns only when finished; re-sending the same PDF is safe and is
    reported as already present, so retrying after a timeout is correct. Because it holds the call
    open that long, it is a good candidate for delegating to a background or sub-agent if you have
    one, so the wait does not block other work. A paper ingested this way lands ONLY in the
    private graph — it will never turn up in search_knowledge_base, so do not read its absence
    there as a failed ingestion. If the account has no private graph these five refuse with a
    message saying so, and no retry will help.

    search_private_knowledge_base, get_private_knowledge_base_overview and
    list_private_knowledge_base_papers each take an optional self_only flag: off by default
    (everyone's papers), set it to restrict to only the papers the caller personally ingested.

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
            "get_knowledge_base_paper_markdown",
            "search_paper_assets",
            "get_paper_asset",
            "ingest_pdf_to_private_knowledge_base",
            "search_private_knowledge_base",
            "get_private_knowledge_base_overview",
            "list_private_knowledge_base_papers",
            "private_knowledge_graph_read",
            "delete_private_knowledge_base_paper",
            "get_private_knowledge_base_paper_markdown",
            "search_private_paper_assets",
            "get_private_paper_asset",
        ]
    ),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)

knowledge_base_service = KnowledgeBaseService()
knowledge_base_asset_service = KnowledgeBaseAssetService()

_AssetKind = Literal["figure", "table"]


def _format_search_results(response: dict[str, Any]) -> str:
    results = response.get("results") or []
    if not results:
        return f"No knowledge base results found for query: {response.get('query', '')!r}"

    lines = [f"Found {response.get('count', len(results))} result(s):\n"]
    for i, result in enumerate(results, start=1):
        metadata = result.get("metadata") or {}
        title = metadata.get("paper_title")
        paper_id = metadata.get("paper_id")
        source = title or paper_id or "unknown source"
        id_suffix = f", id: {paper_id}" if paper_id and title else ""
        lines.append(f"{i}. [source: {source}{id_suffix}, score={result.get('score') or 0:.3f}]\n{result.get('text', '')}\n")
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


def _format_markdown(response: dict[str, Any]) -> str:
    content = response.get("content")
    if content:
        return content
    return f"{response.get('title') or 'This paper'!r} has no reconstructable content."


@mcp.tool(
    name="get_knowledge_base_paper_markdown",
    description=(
        "Reconstruct one paper's full content as markdown, in reading order, from Axiomatic's "
        "curated knowledge base: section headings, passage text, figure captions, table content "
        "and captions, then references under a final References heading.\n\n"
        "Takes the paper's id — get it from a knowledge_graph_read result, e.g. "
        "MATCH (p:Paper) RETURN p.id AS paper_id, p.title AS title."
    ),
    tags=["knowledge-base", "papers", "markdown"],
)
async def get_knowledge_base_paper_markdown(
    doc_id: Annotated[str, "The paper's id, e.g. from a knowledge_graph_read result"],
) -> ToolResult:
    """Reconstruct one paper's full content as markdown, from the curated knowledge base."""
    try:
        response = knowledge_base_service.get_markdown(doc_id)
    except Exception as e:
        raise ToolError(f"Failed to fetch markdown for paper {doc_id!r}: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_markdown(response))],
        structured_content=response,
    )


def _format_asset_matches(matches: list[dict[str, Any]], kind: _AssetKind, fetch_tool_name: str) -> str:
    if not matches:
        return f"No {kind}s in this paper matched that query."
    lines = [f"Found {len(matches)} {kind}(s):"]
    for match in matches:
        lines.append(f"  - seq {match.get('seq')}: {match.get('caption')}")
    lines.append(f"Fetch one with {fetch_tool_name}(doc_id=..., kind={kind!r}, seq=<seq>).")
    return "\n".join(lines)


@mcp.tool(
    name="search_paper_assets",
    description=(
        "Find figures or tables in one paper of Axiomatic's curated knowledge base whose caption "
        "matches a query, ranked by relevance. Returns each match's position (seq) and caption; "
        "fetch the actual figure or table with get_paper_asset.\n\n"
        "query is Lucene query syntax, not a plain string, e.g. "
        "'\"fig 4\"^5 OR \"figure 4\"^5 OR neural network architecture'."
    ),
    tags=["knowledge-base", "papers", "figures", "tables", "search"],
)
async def search_paper_assets(
    doc_id: Annotated[str, "The paper's id, e.g. from a knowledge_graph_read or search_knowledge_base result"],
    kind: Annotated[_AssetKind, "Which kind of asset to search for"],
    query: Annotated[str, "Lucene query syntax matched against the caption, e.g. '\"fig 4\"^5 OR neural network architecture'"],
    limit: Annotated[int, "Maximum number of matches to return (1-50)"] = 5,
) -> ToolResult:
    """Find figures or tables in one paper of the curated knowledge base, by caption."""
    try:
        matches = (
            knowledge_base_asset_service.search_figures(doc_id, query, limit)
            if kind == "figure"
            else knowledge_base_asset_service.search_tables(doc_id, query, limit)
        )
    except Exception as e:
        raise ToolError(f"Failed to search {kind}s in paper {doc_id!r}: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_asset_matches(matches, kind, "get_paper_asset"))],
        structured_content={"matches": matches},
    )


@mcp.tool(
    name="get_paper_asset",
    description=(
        "Download one figure or table from a paper in Axiomatic's curated knowledge base, "
        "addressed by its position in the document (seq, from search_paper_assets). A figure "
        "comes back as an image the model can view directly; a table comes back as markdown. "
        "Figures have no size cap, so a large scientific figure can be a large response."
    ),
    tags=["knowledge-base", "papers", "figures", "tables"],
)
async def get_paper_asset(
    doc_id: Annotated[str, "The paper's id"],
    kind: Annotated[_AssetKind, "Which kind of asset to fetch"],
    seq: Annotated[int, "The asset's position in the document, from search_paper_assets"],
) -> ToolResult:
    """Download one figure or table from a paper in the curated knowledge base."""
    try:
        if kind == "figure":
            image_bytes, content_type = knowledge_base_asset_service.get_figure(doc_id, seq)
            content: list[Any] = [
                ImageContent(type="image", data=base64.b64encode(image_bytes).decode("ascii"), mimeType=content_type)
            ]
            structured = {"doc_id": doc_id, "seq": seq, "kind": kind, "content_type": content_type}
        else:
            markdown = knowledge_base_asset_service.get_table(doc_id, seq)
            content = [TextContent(type="text", text=markdown)]
            structured = {"doc_id": doc_id, "seq": seq, "kind": kind, "markdown": markdown}
    except Exception as e:
        raise ToolError(f"Failed to fetch {kind} {seq} from paper {doc_id!r}: {e!s}") from e

    return ToolResult(content=content, structured_content=structured)


# --- Private graph ----------------------------------------------------------------------------

_PDF_CONTENT_TYPE = "application/pdf"


def _format_ingest(response: dict[str, Any]) -> str:
    paper_id = response.get("paper_id") or "unknown id"
    title = response.get("title") or "untitled"

    if response.get("already_present"):
        return f"{title!r} ({paper_id}) was already in the private knowledge graph. Nothing was re-ingested — the paper is already queryable."

    lines = [f"Ingested {title!r} into the private knowledge graph as {paper_id}."]
    stored = response.get("pdf_and_figures_stored", response.get("pdf_stored", True))
    if not stored:
        lines.append(
            "The source PDF and/or its figures did not finish uploading, so they cannot be downloaded again. "
            "The paper itself is queryable; sending the same file again completes the upload."
        )
    lines.append("Verify with search_private_knowledge_base — an ingested paper never appears in search_knowledge_base.")
    return "\n".join(lines)


@mcp.tool(
    name="ingest_pdf_to_private_knowledge_base",
    description=(
        "Ingest one local PDF into the organization's private knowledge graph. The PDF is parsed into "
        "passages, figures, tables and references, and the source PDF is stored. This is one of two tools "
        "that write to a knowledge graph — delete_private_knowledge_base_paper is the other — and the "
        "private graph is the only graph either writes to: an ingested paper is reachable through "
        "search_private_knowledge_base and private_knowledge_graph_read, and never through "
        "search_knowledge_base.\n\n"
        "Synchronous and slow: it returns when ingestion has finished, which takes minutes for a full paper. "
        "Re-sending the same PDF is safe — it is reported as already present rather than ingested twice — so "
        "on a timeout or an unclear failure, retrying is the correct move.\n\n"
        "Before writing, this tool raises an MCP elicitation asking the user to confirm the file name and "
        "the destination graph. A decline, a cancel, or a client that does not support elicitation at all "
        "writes nothing and comes back as a plain non-error result — do not retry any of these without a "
        "genuinely fresh reason to think the answer would differ; a client that lacks elicitation support "
        "will fail the same way every time."
    ),
    tags=["knowledge-base", "private", "ingest", "write"],
)
async def ingest_pdf_to_private_knowledge_base(
    ctx: Context,
    file_path: Annotated[Path, "The absolute path to the PDF file to ingest"],
    doi: Annotated[str, "The paper's DOI, if known. Leave empty if unknown."] = "",
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

    if not ctx.session.check_client_capability(ClientCapabilities(elicitation=ElicitationCapability())):
        return ToolResult(
            content=[
                TextContent(
                    type="text",
                    text=(
                        f"Could not ask for confirmation before ingesting {path.name!r}: this client did not "
                        "declare support for MCP elicitation. Nothing was written. Retrying will not help — "
                        "either get the user's go-ahead and ingest from a client that supports elicitation, "
                        "or don't call this tool for this file."
                    ),
                )
            ],
            structured_content={"ingested": False, "action": "unsupported"},
        )

    try:
        confirmation = await ctx.elicit(
            message=f"Ingest {path.name!r} into your organization's private knowledge graph?",
            response_type=None,
        )
    except McpError as e:
        raise ToolError(f"Failed to get the user's confirmation before ingesting {path.name!r}: {e.error.message}") from e
    if confirmation.action != "accept":
        return ToolResult(
            content=[TextContent(type="text", text=f"Ingestion of {path.name!r} was declined; nothing was written.")],
            structured_content={"ingested": False, "action": confirmation.action},
        )

    try:
        # Choose to pass by `asyncio.to_thread` just for the ingest
        response = await asyncio.to_thread(knowledge_base_service.private_ingest, path.name, pdf_bytes, doi)
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
        "ingest_pdf_to_private_knowledge_base; use search_knowledge_base for the curated corpus.\n\n"
        "By default this searches every paper in the organization's private graph, regardless of who "
        "ingested it. Set self_only=True to restrict results to only the papers the caller personally "
        "ingested."
    ),
    tags=["knowledge-base", "private", "search", "citations"],
)
async def search_private_knowledge_base(
    query: Annotated[str, "Natural language question or topic to search for"],
    limit: Annotated[int, "Maximum number of passages to return (1-50)"] = 5,
    self_only: Annotated[bool, "Restrict results to only papers the caller personally ingested"] = False,
) -> ToolResult:
    """Semantic search over the private knowledge base."""
    try:
        response = knowledge_base_service.private_search(query, limit, self_only)
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
        "whether it holds anything at all — before searching or querying it.\n\n"
        "By default this counts every paper in the organization's private graph, regardless of who "
        "ingested it. Set self_only=True to restrict the counts to only the papers the caller "
        "personally ingested."
    ),
    tags=["knowledge-base", "private", "overview"],
)
async def get_private_knowledge_base_overview(
    self_only: Annotated[bool, "Restrict counts to only papers the caller personally ingested"] = False,
) -> ToolResult:
    """Node counts per label in the private knowledge graph."""
    try:
        response = knowledge_base_service.private_overview(self_only)
    except Exception as e:
        raise ToolError(f"Failed to retrieve the private knowledge base overview: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_overview(response))],
        structured_content=response,
    )


def _format_papers(response: dict[str, Any]) -> str:
    items = response.get("items") or []
    total = response.get("total", len(items))
    if not items:
        if total:
            return (
                f"{total} paper(s) total, but page {response.get('page', 1)} of "
                f"{response.get('total_pages', 1)} has none. Call again with a lower page number."
            )
        return "The private knowledge graph holds no papers."

    lines = [
        f"{total} paper(s) total, page {response.get('page', 1)} of "
        f"{response.get('total_pages', 1)} (page size {response.get('page_size', len(items))}), "
        "most recently ingested first:"
    ]
    for item in items:
        lines.append(f"  - {item.get('title') or 'untitled'} (id: {item.get('id')}), " f"ingested {item.get('ingestion_date') or 'unknown date'}")
    if response.get("page", 1) < response.get("total_pages", 1):
        lines.append("More papers exist — call again with a higher page to see the rest.")
    return "\n".join(lines)


@mcp.tool(
    name="list_private_knowledge_base_papers",
    description=(
        "List the papers in the organization's private knowledge graph: id, title and ingestion "
        "date, most recent first. Use it to see what has been ingested without running a search "
        "or a Cypher query, and to get a paper's id for delete_private_knowledge_base_paper.\n\n"
        "By default this lists every paper in the organization's private graph, regardless of "
        "who ingested it. Set self_only=True to restrict the list to only the papers the caller "
        "personally ingested. Results are paginated; check total_pages in the structured result "
        "and increase page to see more."
    ),
    tags=["knowledge-base", "private", "papers"],
)
async def list_private_knowledge_base_papers(
    self_only: Annotated[bool, "Restrict to papers the caller personally ingested"] = False,
    page: Annotated[int, "Page number, starting at 1"] = 1,
    page_size: Annotated[int, "Papers per page (1-100)"] = 20,
) -> ToolResult:
    """List the papers in the private knowledge graph."""
    try:
        response = knowledge_base_service.private_papers(self_only, page, page_size)
    except Exception as e:
        raise ToolError(f"Failed to list the private knowledge base papers: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_papers(response))],
        structured_content=response,
    )


def _format_deletion(response: dict[str, Any]) -> str:
    paper_id = response.get("paper_id")
    if response.get("fully_deleted"):
        lines = [f"Paper {paper_id!r} was deleted from the private knowledge graph, along with everything under it."]
        if not response.get("pdf_and_figures_removed"):
            lines.append(
                "The stored PDF and/or its figures could not be removed and may still be present in storage; "
                "the paper itself is gone from the graph and no longer queryable."
            )
        return "\n".join(lines)
    return (
        f"You were removed as an owner of paper {paper_id!r}. Other owners remain, so the paper "
        "itself was not deleted and is still queryable by them."
    )


@mcp.tool(
    name="delete_private_knowledge_base_paper",
    description=(
        "Remove yourself as an owner of one paper in the organization's private knowledge graph. "
        "When you are its last owner, the paper and everything under it (passages, figures, "
        "tables, references, the stored PDF) is deleted outright; otherwise only your ownership "
        "is removed and the paper remains for its other owners.\n\n"
        "Identify the paper by its id — get it from list_private_knowledge_base_papers or from a "
        "search_private_knowledge_base result's metadata, never guess or construct one.\n\n"
        "Before deleting, this tool raises an MCP elicitation asking the user to confirm the paper. A "
        "decline, a cancel, or a client that does not support elicitation at all deletes nothing and "
        "comes back as a plain non-error result — do not retry any of these without a genuinely fresh "
        "reason to think the answer would differ; a client that lacks elicitation support will fail the "
        "same way every time."
    ),
    tags=["knowledge-base", "private", "papers", "delete", "write"],
)
async def delete_private_knowledge_base_paper(
    ctx: Context,
    doc_id: Annotated[str, "The paper's id, as returned by list_private_knowledge_base_papers or search_private_knowledge_base"],
) -> ToolResult:
    """Remove the caller's ownership of one paper in the private knowledge graph, by id."""
    if not ctx.session.check_client_capability(ClientCapabilities(elicitation=ElicitationCapability())):
        return ToolResult(
            content=[
                TextContent(
                    type="text",
                    text=(
                        f"Could not ask for confirmation before deleting paper {doc_id!r}: this client did not "
                        "declare support for MCP elicitation. Nothing was deleted. Retrying will not help — "
                        "either get the user's go-ahead and delete from a client that supports elicitation, "
                        "or don't call this tool for this paper."
                    ),
                )
            ],
            structured_content={"deleted": False, "action": "unsupported"},
        )

    try:
        confirmation = await ctx.elicit(
            message=(
                f"Remove your ownership of paper {doc_id!r} in your organization's private knowledge graph? "
                "If you are its last owner, this also deletes the paper and everything under it (passages, "
                "figures, tables, references, the stored PDF)."
            ),
            response_type=None,
        )
    except McpError as e:
        raise ToolError(f"Failed to get the user's confirmation before deleting paper {doc_id!r}: {e.error.message}") from e
    if confirmation.action != "accept":
        return ToolResult(
            content=[TextContent(type="text", text=f"Deletion of paper {doc_id!r} was declined; nothing was deleted.")],
            structured_content={"deleted": False, "action": confirmation.action},
        )

    try:
        response = knowledge_base_service.private_delete_paper(doc_id)
    except Exception as e:
        raise ToolError(f"Failed to delete paper {doc_id!r}: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_deletion(response))],
        structured_content=response,
    )


@mcp.tool(
    name="search_private_paper_assets",
    description=(
        "Find figures or tables in one paper of the organization's private knowledge graph whose "
        "caption matches a query, ranked by relevance. The private counterpart of "
        "search_paper_assets: same query rules, same result shape, different graph. Fetch the "
        "actual figure or table with get_private_paper_asset.\n\n"
        "query is Lucene query syntax, not a plain string, e.g. "
        "'\"fig 4\"^5 OR \"figure 4\"^5 OR neural network architecture'."
    ),
    tags=["knowledge-base", "private", "papers", "figures", "tables", "search"],
)
async def search_private_paper_assets(
    doc_id: Annotated[str, "The paper's id, as returned by list_private_knowledge_base_papers or search_private_knowledge_base"],
    kind: Annotated[_AssetKind, "Which kind of asset to search for"],
    query: Annotated[str, "Lucene query syntax matched against the caption, e.g. '\"fig 4\"^5 OR neural network architecture'"],
    limit: Annotated[int, "Maximum number of matches to return (1-50)"] = 5,
) -> ToolResult:
    """Find figures or tables in one paper of the private knowledge graph, by caption."""
    try:
        matches = (
            knowledge_base_asset_service.private_search_figures(doc_id, query, limit)
            if kind == "figure"
            else knowledge_base_asset_service.private_search_tables(doc_id, query, limit)
        )
    except Exception as e:
        raise ToolError(f"Failed to search {kind}s in paper {doc_id!r}: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_asset_matches(matches, kind, "get_private_paper_asset"))],
        structured_content={"matches": matches},
    )


@mcp.tool(
    name="get_private_paper_asset",
    description=(
        "Download one figure or table from a paper in the organization's private knowledge "
        "graph, addressed by its position in the document (seq, from search_private_paper_assets). "
        "The private counterpart of get_paper_asset: a figure comes back as an image the model "
        "can view directly, a table as markdown. Figures have no size cap, so a large scientific "
        "figure can be a large response."
    ),
    tags=["knowledge-base", "private", "papers", "figures", "tables"],
)
async def get_private_paper_asset(
    doc_id: Annotated[str, "The paper's id"],
    kind: Annotated[_AssetKind, "Which kind of asset to fetch"],
    seq: Annotated[int, "The asset's position in the document, from search_private_paper_assets"],
) -> ToolResult:
    """Download one figure or table from a paper in the private knowledge graph."""
    try:
        if kind == "figure":
            image_bytes, content_type = knowledge_base_asset_service.private_get_figure(doc_id, seq)
            content: list[Any] = [
                ImageContent(type="image", data=base64.b64encode(image_bytes).decode("ascii"), mimeType=content_type)
            ]
            structured = {"doc_id": doc_id, "seq": seq, "kind": kind, "content_type": content_type}
        else:
            markdown = knowledge_base_asset_service.private_get_table(doc_id, seq)
            content = [TextContent(type="text", text=markdown)]
            structured = {"doc_id": doc_id, "seq": seq, "kind": kind, "markdown": markdown}
    except Exception as e:
        raise ToolError(f"Failed to fetch {kind} {seq} from paper {doc_id!r}: {e!s}") from e

    return ToolResult(content=content, structured_content=structured)


@mcp.tool(
    name="get_private_knowledge_base_paper_markdown",
    description=(
        "Reconstruct one paper's full content as markdown, in reading order, from the "
        "organization's private knowledge graph. Same rendering as "
        "get_knowledge_base_paper_markdown, different graph.\n\n"
        "Takes the paper's id — get it from list_private_knowledge_base_papers or from a "
        "search_private_knowledge_base result's metadata."
    ),
    tags=["knowledge-base", "private", "papers", "markdown"],
)
async def get_private_knowledge_base_paper_markdown(
    doc_id: Annotated[str, "The paper's id, as returned by list_private_knowledge_base_papers or search_private_knowledge_base"],
) -> ToolResult:
    """Reconstruct one paper's full content as markdown, from the private knowledge graph."""
    try:
        response = knowledge_base_service.private_get_markdown(doc_id)
    except Exception as e:
        raise ToolError(f"Failed to fetch markdown for paper {doc_id!r}: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_markdown(response))],
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
