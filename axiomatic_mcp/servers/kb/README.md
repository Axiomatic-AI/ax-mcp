# AxKnowledgeBase Server

An MCP server that exposes Axiomatic's curated Knowledge Base — scientific papers, extracted entities (devices, materials, performance metrics), and passages retrieved via semantic search.

## Overview

The Knowledge Base server lets AI assistants query Axiomatic's context-curated corpus instead of relying on unsourced recollection of "standard results from the literature". Every search result carries its provenance (paper id/title), so answers can be cited and vetted precisely. Graph rows are the exception: a Cypher query returns exactly the columns it asks for, so provenance there is the query's job — see `knowledge_graph_read`.

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

### `knowledge_graph_read`

Run one read-only Cypher query against the knowledge graph and get the rows back as a table. Use it when the answer has to be tabular — comparing devices across metrics, building a dataframe, plotting — rather than the prose passages `search_knowledge_base` returns. Call `get_knowledge_base_schema` first for the labels and property names.

**Parameters:**

- `query` (str, required): a read-only Cypher MATCH/RETURN query, aliasing individual properties (`RETURN n.name AS name`, never a bare `RETURN n`)
- `params` (dict, optional): query parameters, for safe value injection

**Provenance is the query's job.** Rows carry only what the RETURN clause names, so every query should also return the paper each row came from. `Entity`, `Statement` and `Passage` all carry `doc_id`, so the source is one index seek away — no need to walk `HAS_PASSAGE`/`HAS_STATEMENT`/`HAS_ENTITY`:

```cypher
MATCH (e:Entity) WHERE e.name CONTAINS $term
MATCH (p:Document {id: e.doc_id})
RETURN e.name AS name, p.id AS paper_id, p.title AS title
```

A result with no `paper_id`/`doc_id` column is labelled uncited in the response.

**Keep results small.** The whole result comes back in one MCP response, so return only the properties you need, add an explicit `LIMIT` (100 rows is usually plenty), and never select an `embedding_*` property or bulk `Passage.text`.

**Example Usage:**

```
What does our knowledge base say about ring resonator loss mechanisms? Cite your sources.
```

```
Table the coupling efficiency of every grating coupler in the knowledge base, with its source paper.
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
- `knowledge_graph_read` enforces provenance only by convention: the response flags rows whose columns don't look like a paper id, but an unusual alias can slip past the check either way. ax-stack traces provenance cell by cell for its own agent tools, but the `/neo4j/execute-read` endpoint doesn't return that trace, so it can't be enforced here
- The rendered table is bounded — cells over 200 characters are elided and the table stops at 10,000 characters, both stated in the output. The structured result still carries every row in full, so a query selecting long text properties can still produce a large response; keep a `LIMIT` on it
- Looking up a specific paper by title, downloading a paper's PDF, and subgraph visualization exist as internal agent tools in ax-stack but aren't exposed here yet — they need backend endpoints that don't exist today (paper lookup and download aren't REST-exposed)
