"""Service for Axiomatic's Knowledge Base figure/table endpoints."""

from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class KnowledgeBaseAssetService(SingletonBase):
    """Thin proxy service for the Axiomatic Knowledge Base figure/table endpoints."""

    def search_figures(self, doc_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Find figures in one paper of the curated knowledge base whose caption matches a Lucene
        query, ranked by relevance.

        Returns:
            list of {seq, caption}
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.KNOWLEDGE_BASE_FIGURE_SEARCH,
                data={"doc_id": doc_id, "query": query, "limit": limit},
            )

    def search_tables(self, doc_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Find tables in one paper of the curated knowledge base whose caption matches a Lucene
        query, ranked by relevance.

        Returns:
            list of {seq, caption}
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.KNOWLEDGE_BASE_TABLE_SEARCH,
                data={"doc_id": doc_id, "query": query, "limit": limit},
            )

    def get_figure(self, doc_id: str, seq: int) -> tuple[bytes, str]:
        """
        Download one figure of a paper in the curated knowledge base, by its position in the
        document.

        Returns:
            (image bytes, content type)
        """
        with AxiomaticAPIClient() as client:
            return client.get_bytes(ApiRoutes.KNOWLEDGE_BASE_FIGURE, params={"doc_id": doc_id, "seq": seq})

    def get_table(self, doc_id: str, seq: int) -> str:
        """
        Download one table of a paper in the curated knowledge base as markdown, by its position
        in the document.

        Returns:
            the table's markdown content
        """
        with AxiomaticAPIClient() as client:
            return client.get_text(ApiRoutes.KNOWLEDGE_BASE_TABLE, params={"doc_id": doc_id, "seq": seq})

    def private_search_figures(self, doc_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Private-graph counterpart of `search_figures`."""
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.KNOWLEDGE_BASE_PRIVATE_FIGURE_SEARCH,
                data={"doc_id": doc_id, "query": query, "limit": limit},
            )

    def private_search_tables(self, doc_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Private-graph counterpart of `search_tables`."""
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.KNOWLEDGE_BASE_PRIVATE_TABLE_SEARCH,
                data={"doc_id": doc_id, "query": query, "limit": limit},
            )

    def private_get_figure(self, doc_id: str, seq: int) -> tuple[bytes, str]:
        """Private-graph counterpart of `get_figure`."""
        with AxiomaticAPIClient() as client:
            return client.get_bytes(ApiRoutes.KNOWLEDGE_BASE_PRIVATE_FIGURE, params={"doc_id": doc_id, "seq": seq})

    def private_get_table(self, doc_id: str, seq: int) -> str:
        """Private-graph counterpart of `get_table`."""
        with AxiomaticAPIClient() as client:
            return client.get_text(ApiRoutes.KNOWLEDGE_BASE_PRIVATE_TABLE, params={"doc_id": doc_id, "seq": seq})
