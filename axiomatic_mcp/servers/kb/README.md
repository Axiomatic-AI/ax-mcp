# AxKnowledgeBase Server

An MCP server that exposes Axiomatic's curated Knowledge Base — scientific papers, extracted entities (devices, materials, performance metrics), and passages retrieved via semantic search.

## Overview

The Knowledge Base server lets AI assistants query Axiomatic's context-curated corpus instead of relying on unsourced recollection of "standard results from the literature". Every search result carries its provenance (paper id/title), so answers can be cited and vetted precisely.

## Tools Available

### `search_knowledge_base`

Semantic search: embed a text query and return the most similar passages, each with its source and similarity score.

**Parameters:**

- `query` (str, required): natural language question or topic
- `limit` (int, optional, default 5): maximum number of passages to return (1-50)

### `get_knowledge_base_schema`

Retrieve the schema: entity types with their properties, and relationship types with their properties and which entity types they connect.

### `get_knowledge_base_overview`

Corpus-level statistics: total papers, total extracted key metrics, and the most common devices and materials. Useful for getting oriented before searching.

### `list_knowledge_base_papers`

Browse the paper corpus directly (paginated), instead of semantic search. Returns each paper's id, title, authors, and how many extracted key metrics reference it.

**Parameters:**

- `page` (int, optional, default 1): page number, starting at 1
- `page_size` (int, optional, default 20): papers per page (1-100)

**Example Usage:**

```
What does our knowledge base say about ring resonator loss mechanisms? Cite your sources.
```

## Installation

### Quick Install (via PyPI)

```json
{
  "axiomatic-kb": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-kb"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Development Install

```json
{
  "axiomatic-kb": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.kb"],
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

- Read-only: no tool writes new content into the knowledge base
- Structured/advanced querying beyond schema-driven search is not yet exposed here — planned as a follow-up
- Looking up a specific paper by title, downloading a paper's PDF, and subgraph visualization exist as internal agent tools in ax-stack but aren't exposed here yet — they need new backend endpoints (paper lookup/download aren't REST-exposed today) or a Cypher-free wrapper (visualization currently takes raw Cypher, which we deliberately don't expose)
