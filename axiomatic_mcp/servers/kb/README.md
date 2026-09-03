# AxKnowledgeBase Server

An MCP server that exposes two knowledge graphs: Axiomatic's curated Knowledge Base — scientific papers, extracted entities (devices, materials, performance metrics), and passages retrieved via semantic search — and your organization's own **private** graph, which you can ingest papers into.

## Overview

The Knowledge Base server lets AI assistants query Axiomatic's context-curated corpus instead of relying on unsourced recollection of "standard results from the literature". Every search result carries its provenance (paper id/title), so answers can be cited and vetted precisely. Graph rows are the exception: a Cypher query returns exactly the columns it asks for, so provenance there is the query's job — see `knowledge_graph_read`.

The two graphs are separate, and which one a question is about matters. The **curated** corpus is Axiomatic's and read-only. The **private** graph holds only what your organization ingested itself; it is the only writable one, and a paper ingested there never appears in the curated-corpus tools. `get_knowledge_base_schema` describes both, since every graph shares one schema.

## Tools Available

### `search_knowledge_base`

Semantic search: embed a text query and return the most similar passages, each with its source and similarity score.

**Parameters:**

- `query` (str, required): natural language question or topic
- `limit` (int, optional, default 5): maximum number of passages to return (1-50)

### `get_knowledge_base_schema`

Retrieve the schema: entity types with their properties, and relationship types with their properties and which entity types they connect.

### `get_knowledge_base_overview`

Corpus-level statistics: the graph's total node count and the breakdown by entity label, largest first. Useful for getting oriented before searching.

A node carrying several labels is counted once per label, so the per-label counts do not sum to the total — the response says so inline.

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

## Private Knowledge Graph

Your organization's own graph. All four tools below return a plain refusal if the account has no private graph, and no retry will help.

### `ingest_pdf_to_private_knowledge_base`

Ingest one local PDF. It is converted to markdown, its statements and entities are extracted, and the source PDF is stored. **This is the only tool in this server that writes to a knowledge graph.**

**Parameters:**

- `file_path` (path, required): absolute path to the PDF
- `title` (str, optional): leave empty to use the PDF's first heading
- `paper_id` (str, optional): leave empty to derive it from a hash of the converted markdown

**It blocks for minutes.** The call returns only when ingestion has finished. If the server's own timeout fires first you get a 504 saying the graph is unchanged — re-sending the same file is safe, and is reported as already present rather than ingested twice, so retrying is always the right move.

Two response states are worth reading rather than skimming: `already_present` means nothing was extracted, so the zero counts are expected; `pdf_stored: false` means the paper is queryable but its source PDF did not finish uploading, and sending the same file again completes it.

The PDF's bytes are sniffed before upload, so a non-PDF with a `.pdf` name is refused in milliseconds instead of after a multi-minute request.

### `search_private_knowledge_base`

Semantic search over the private graph. Same parameters and same response shape as `search_knowledge_base` — `query` and `limit` (1-50, default 5) — just a different graph. This is where an ingested paper shows up.

### `get_private_knowledge_base_overview`

Node counts per label in the private graph, with the same caveat about multi-label nodes as the curated one. The quickest way to see whether the private graph holds anything yet.

### `private_knowledge_graph_read`

The private counterpart of `knowledge_graph_read`: same parameters, same query rules, same result shape, different graph. Provenance is still the query's job.

**Example Usage:**

```
Ingest ~/papers/our_measurements.pdf into our private knowledge base, then tell me what it says about coupling losses.
```

```
Compare the grating couplers in our private graph against the ones in Axiomatic's corpus.
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

- The curated corpus is read-only. The only write path anywhere in this server is `ingest_pdf_to_private_knowledge_base`, and it writes only to your organization's private graph
- Ingestion is synchronous and takes minutes for a full paper; there is no job id to poll and no progress reporting, so a client with a short tool timeout may give up before the server answers. Re-sending the same PDF is safe, so the recovery is simply to call it again
- Browsing the corpus paper by paper is now a Cypher query rather than its own tool (`/neo4j/papers` is deprecated on the API): `MATCH (p:Document) RETURN p.id AS paper_id, p.title AS title ORDER BY p.title LIMIT 50`, paginating with `SKIP`. The one thing genuinely lost with the old `list_knowledge_base_papers` is its per-paper `keyMetricCount`, which now has to be rebuilt with a `count{}` over each paper's key-metric relationships
- `knowledge_graph_read` enforces provenance only by convention: the response flags rows whose columns don't look like a paper id, but an unusual alias can slip past the check either way. ax-stack traces provenance cell by cell for its own agent tools, but the `/neo4j/execute-read` endpoint doesn't return that trace, so it can't be enforced here
- The rendered table is bounded — cells over 200 characters are elided and the table stops at 10,000 characters, both stated in the output. The structured result still carries every row in full, so a query selecting long text properties can still produce a large response; keep a `LIMIT` on it
- Looking up a specific paper by title, downloading a paper's PDF, and subgraph visualization exist as internal agent tools in ax-stack but aren't exposed here yet — they need backend endpoints that don't exist today (paper lookup and download aren't REST-exposed)
