from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class PdkService(SingletonBase):
    def list_pdks(self) -> dict[str, Any]:
        all_pdks = AxiomaticAPIClient().get(ApiRoutes.PDK_LIST)
        available_pdks = AxiomaticAPIClient().get(ApiRoutes.PDK_PERMISSION)

        permissions = available_pdks.get("permissions", [])

        for p in all_pdks.get("pdks", []):
            granted = any(perm.get("pdk_type") == p.get("pdk_type") and perm.get("status") == "granted" for perm in permissions)
            p["granted"] = granted

        return all_pdks

    def get_pdk_info(self, pdk_type: str):
        response = AxiomaticAPIClient().get(ApiRoutes.PDK_INFO.format(pdk_type=pdk_type))
        return response
