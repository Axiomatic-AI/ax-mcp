# AxPaperSearch Server

An MCP server that searches scientific literature on arXiv and OpenAlex.

## Overview

The Paper Search server lets AI assistants find the primary source for a claim instead of relying on memorized results, and download papers to use as direct context — the same "find tex/PDF sources, then work from them" workflow Axiomatic researchers do manually today.

## Tools Available

### `search_arxiv`

Search arXiv for preprints. Returns titles, authors, abstracts, and direct PDF links.

**Parameters:**

- `query` (str, required): arXiv search query
- `max_results` (int, optional, default 10)
- `sort_by` (str, optional, default `relevance`): one of `relevance`, `lastUpdatedDate`, `submittedDate`
- `sort_order` (str, optional, default `descending`): one of `ascending`, `descending`

### `search_openalex`

Search OpenAlex for scholarly works. Broader coverage than arXiv (published venues, DOIs, citation counts) — useful for checking how well-established a claim actually is in the literature.

**Parameters:**

- `query` (str, required): OpenAlex search query
- `limit` (int, optional, default 25)

**Example Usage:**

```
Find the arXiv paper this design is based on and download its PDF as context.
```

## Installation

### Quick Install (via PyPI)

```json
{
  "axiomatic-paper-search": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-paper-search"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Development Install

```json
{
  "axiomatic-paper-search": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.paper_search"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

## Configuration

### Required Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)

## Limitations

- PDF/tex download tools are not yet wired in — planned as a follow-up (currently returns links only)
