"""Service for Axiomatic's Knowledge Base API calls."""

from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class KnowledgeBaseService(SingletonBase):
    """Thin proxy service for the Axiomatic Knowledge Base endpoints."""

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        """
        Semantic search over the knowledge base: embed a text query and return the
        most similar source passages, each with its provenance (paper id/title).

        Returns:
            dict with keys: query, results (list of {text, score, metadata}), count
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.KNOWLEDGE_BASE_SEARCH,
                data={"query": query, "limit": limit},
            )

    def get_schema(self) -> dict[str, Any]:
        """
        Retrieve the knowledge base schema (entity types and their properties, and
        relationship types between them).

        Returns:
            dict with keys: nodes, relationships
        """
        with AxiomaticAPIClient() as client:
            return client.post(ApiRoutes.KNOWLEDGE_BASE_GET_SCHEMA)

    def get_overview(self) -> dict[str, Any]:
        """
        Retrieve summary statistics for the knowledge base: total papers, total key
        metrics, and the most common devices and materials.

        Returns:
            dict with keys: total_papers, total_key_metrics, devices, materials
        """
        with AxiomaticAPIClient() as client:
            return client.get(ApiRoutes.KNOWLEDGE_BASE_OVERVIEW)

    def execute_read(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Run one read-only Cypher query against the knowledge graph.

        The endpoint enforces read-only, a server-side query timeout and a row cap, and
        reports the cap through `truncated` rather than by failing.

        Returns:
            dict with keys: schema_kind, columns, rows, count, truncated
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.KNOWLEDGE_BASE_EXECUTE_READ,
                data={"query": query, "params": params},
            )

    def private_search(self, query: str, limit: int = 5) -> dict[str, Any]:
        """
        Semantic search over the organization's private knowledge base.

        Same response shape as `search`, so the same formatter renders it.

        Returns:
            dict with keys: query, results (list of {text, score, metadata}), count
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.KNOWLEDGE_BASE_PRIVATE_SEARCH,
                data={"query": query, "limit": limit},
            )

    def private_overview(self) -> dict[str, Any]:
        """
        Node counts per label in the organization's private knowledge graph.

        Returns:
            dict with keys: items (list of {label, count}, largest first), total
        """
        with AxiomaticAPIClient() as client:
            return client.get(ApiRoutes.KNOWLEDGE_BASE_PRIVATE_OVERVIEW)

    def private_execute_read(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Run one read-only Cypher query against the organization's private knowledge graph.

        Same guarantees and response shape as `execute_read`.

        Returns:
            dict with keys: schema_kind, columns, rows, count, truncated
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.KNOWLEDGE_BASE_PRIVATE_EXECUTE_READ,
                data={"query": query, "params": params},
            )

    def private_ingest(self, file_name: str, pdf_bytes: bytes, title: str = "", paper_id: str = "") -> dict[str, Any]:
        """
        Ingest one PDF into the organization's private knowledge graph.

        Returns:
            dict with keys: paper_id, title, already_present, pdf_stored, passages, entities,
            statements
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.KNOWLEDGE_BASE_PRIVATE_INGEST,
                files={"file": (file_name, pdf_bytes, "application/pdf")},
                data={"title": title, "paper_id": paper_id},
            )
