import re
from typing import Any


def flatten_pdks_response(pdk_response: dict[str, Any], only_granted: bool = True) -> list[str]:
    final_pdk_types: list[str] = []
    pdk_list = pdk_response.get("pdks", [])

    for pdk_info in pdk_list:
        pdk_type = pdk_info.get("pdk_type")

        if not only_granted or bool(pdk_info.get("granted")):
            final_pdk_types.append(str(pdk_type))

    return final_pdk_types


def extract_pdk_type_from_code(code: str) -> str | None:
    pattern = re.compile(r"^\s*(?:import|from)\s+([a-zA-Z0-9_.]+)", re.MULTILINE)
    matches = pattern.findall(code)
    for match in matches:
        if match.startswith("cspdk."):
            return match
    return None
