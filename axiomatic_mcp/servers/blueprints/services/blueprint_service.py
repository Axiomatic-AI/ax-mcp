"""Service for Axiomatic's blueprint API calls."""

from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class BlueprintService(SingletonBase):
    """Thin proxy service for the Axiomatic blueprint endpoints."""

    def list_blueprints(self, domain: str | None = None, status: str | None = None) -> dict[str, Any]:
        """
        The blueprint catalog, optionally narrowed to one domain and/or one lifecycle status.

        Returns:
            dict with keys: items (list of {id, domain, name, component_type, status, version,
            n_optical, n_electrical, available_sections}), total
        """
        params = {k: v for k, v in {"domain": domain, "status": status}.items() if v is not None}
        with AxiomaticAPIClient() as client:
            return client.get(ApiRoutes.BLUEPRINTS_LIST, params=params)

    def get_blueprint(self, domain: str, name: str, sections: list[str] | None = None) -> dict[str, Any]:
        """
        One blueprint's contract. With no `sections` the API returns manifest and state.

        httpx sends a list param as a repeated key (`?sections=manifest&sections=state`),
        which is what the endpoint expects.

        Returns:
            dict with the catalog item keys plus manifest (dict, or None if not requested)
            and sections ({section: markdown} for the requested text sections)
        """
        route = ApiRoutes.BLUEPRINTS_GET.format(domain=domain, name=name)
        with AxiomaticAPIClient() as client:
            return client.get(route, params={"sections": sections} if sections else None)
