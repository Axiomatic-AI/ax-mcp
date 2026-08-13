"""AxPaperSearch MCP server — search arXiv and OpenAlex for scientific papers."""

from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .services.paper_search_service import PaperSearchService

mcp = FastMCP(
    name="AxPaperSearch Server",
    instructions="""This server searches scientific literature on arXiv and OpenAlex.
    Use search_arxiv for preprints (returns abstract text and a direct PDF link, ideal for
    downloading tex/PDF sources as context). Use search_openalex for broader scholarly coverage
    (published venues, DOIs, citation counts). Prefer these over relying on memorized/unsourced
    claims about "standard results from the literature".
    """ + get_feedback_prompt(["search_arxiv", "search_openalex"]),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)

paper_search_service = PaperSearchService()


def _format_arxiv_results(response: dict[str, Any]) -> str:
    papers = response.get("papers") or []
    if not papers:
        return f"No arXiv results found for query: {response.get('query', '')!r}"

    lines = [f"Found {len(papers)} of {response.get('total_results', len(papers))} total arXiv result(s):\n"]
    for i, paper in enumerate(papers, start=1):
        authors = ", ".join(paper.get("authors") or []) or "unknown authors"
        summary = (paper.get("summary") or "").strip().replace("\n", " ")
        summary_preview = summary[:280] + ("..." if len(summary) > 280 else "")
        lines.append(
            f"{i}. {paper.get('title', 'untitled')} ({paper.get('arxiv_id', '')})\n"
            f"   Authors: {authors}\n"
            f"   PDF: {paper.get('pdf_url', 'n/a')}\n"
            f"   {summary_preview}\n"
        )
    return "\n".join(lines)


def _format_openalex_results(response: dict[str, Any]) -> str:
    results = response.get("results") or []
    if not results:
        return "No OpenAlex results found."

    lines = [f"Found {len(results)} OpenAlex result(s):\n"]
    for i, work in enumerate(results, start=1):
        authors = ", ".join(a.get("name", "") for a in work.get("authors") or []) or "unknown authors"
        oa = "open access" if work.get("open_access") else "closed access"
        lines.append(
            f"{i}. {work.get('title', 'untitled')} (doi: {work.get('doi', 'n/a')})\n"
            f"   Authors: {authors}\n"
            f"   {work.get('publication_date', 'n/a')}, cited {work.get('cited_by_count', 0)} times, {oa}\n"
        )
    return "\n".join(lines)


@mcp.tool(
    name="search_arxiv",
    description=(
        "Search arXiv for preprints matching a query. Returns titles, authors, abstracts, and "
        "direct PDF links. Useful for finding the primary source of a claim, or for downloading "
        "papers to use as context instead of relying on memorized 'standard results'."
    ),
    tags=["papers", "arxiv", "search"],
)
async def search_arxiv(
    query: Annotated[str, "arXiv search query, e.g. 'inverse design photonic waveguide'"],
    max_results: Annotated[int, "Maximum number of results to return"] = 10,
    sort_by: Annotated[str, "One of: relevance, lastUpdatedDate, submittedDate"] = "relevance",
    sort_order: Annotated[str, "One of: ascending, descending"] = "descending",
) -> ToolResult:
    """Search arXiv for papers."""
    try:
        response = paper_search_service.search_arxiv(query, max_results, sort_by, sort_order)
    except Exception as e:
        raise ToolError(f"Failed to search arXiv: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_arxiv_results(response))],
        structured_content=response,
    )


@mcp.tool(
    name="search_openalex",
    description=(
        "Search OpenAlex for scholarly works matching a query. Broader coverage than arXiv "
        "(published venues, DOIs, citation counts). Useful for cross-checking whether a claim is "
        "actually well established in the literature, and by how much it is cited."
    ),
    tags=["papers", "openalex", "search"],
)
async def search_openalex(
    query: Annotated[str, "OpenAlex search query, e.g. 'inverse design photonic waveguide'"],
    limit: Annotated[int, "Maximum number of results to return"] = 25,
) -> ToolResult:
    """Search OpenAlex for scholarly works."""
    try:
        response = paper_search_service.search_openalex(query, limit)
    except Exception as e:
        raise ToolError(f"Failed to search OpenAlex: {e!s}") from e

    return ToolResult(
        content=[TextContent(type="text", text=_format_openalex_results(response))],
        structured_content=response,
    )
