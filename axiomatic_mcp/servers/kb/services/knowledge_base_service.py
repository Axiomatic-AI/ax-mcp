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

    def list_papers(self, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        """
        List papers ingested into the knowledge base, paginated.

        Returns:
            dict with keys: items (list of {paper_id, title, authors, keyMetricCount}),
            total, page, page_size, total_pages
        """
        with AxiomaticAPIClient() as client:
            return client.get(
                ApiRoutes.KNOWLEDGE_BASE_LIST_PAPERS,
                params={"page": page, "page_size": page_size},
            )
