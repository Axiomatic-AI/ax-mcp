"""Service for arXiv and OpenAlex paper search API calls."""

from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class PaperSearchService(SingletonBase):
    """Thin proxy service for the Axiomatic arXiv/OpenAlex search endpoints."""

    def search_arxiv(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
    ) -> dict[str, Any]:
        """
        Search arXiv for papers.

        Returns:
            dict with keys: papers (list of {arxiv_id, title, summary, authors, published,
            updated, categories, abs_url, pdf_url}), total_results, query
        """
        with AxiomaticAPIClient() as client:
            return client.get(
                ApiRoutes.ARXIV_SEARCH_WORKS,
                params={
                    "query": query,
                    "max_results": max_results,
                    "sort_by": sort_by,
                    "sort_order": sort_order,
                },
            )

    def search_openalex(self, query: str, limit: int = 25) -> dict[str, Any]:
        """
        Search OpenAlex for scholarly works.

        Returns:
            dict with key: results (list of {id, title, abstract, publication_date, type,
            doi, open_access, cited_by_count, authors})
        """
        with AxiomaticAPIClient() as client:
            return client.get(
                ApiRoutes.OPENALEX_SEARCH_WORKS,
                params={"query": query, "limit": limit},
            )
