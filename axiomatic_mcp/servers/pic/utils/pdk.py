from typing import Any


def flatten_pdks_response(pdk_response: dict[str, Any], only_granted: bool = True) -> list[str]:
    final_pdk_types: list[str] = []
    pdk_list = pdk_response.get("pdks", [])

    for pdk_info in pdk_list:
        pdk_type = pdk_info.get("pdk_type")

        if not only_granted or bool(pdk_info.get("granted")):
            final_pdk_types.append(str(pdk_type))

    return final_pdk_types
