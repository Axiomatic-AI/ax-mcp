import math
from typing import Any

from ..utils.physics import get_linear_range, str_units_to_um


def get_wavelengths_from_statements(statements: list[dict[str, Any]], num_points: int = 10000) -> list[float] | None:
    all_values = _parse_all_wavelengths(statements)
    if not all_values:
        return None

    min_w = min(all_values)
    max_w = max(all_values)

    if min_w == max_w:
        return get_wavelengths_from_single_value(min_w, num_points)
    return get_wavelengths_from_bounds(min_w, max_w, num_points)


def get_default_wavelength_range(num_points: int = 10000) -> list[float]:
    center = 1.55
    span = 0.01
    return get_linear_range(center - span, center + span, num_points)


def get_wavelengths_from_bounds(min_val: float, max_val: float, num_points: int = 10000) -> list[float]:
    return get_linear_range(min_val, max_val, num_points)


def get_wavelengths_from_single_value(value: float, num_points: int = 10000) -> list[float]:
    delta = value * 0.1
    return get_linear_range(value - delta, value + delta, num_points)


def _parse_all_wavelengths(statements: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []

    def process_value(val_str: Any) -> None:
        try:
            num = str_units_to_um(val_str)
            if math.isfinite(num):
                values.append(num)
        except Exception:
            pass

    for statement in statements:
        mappings = statement.get("formalization", {}).get("mapping", {})
        if not isinstance(mappings, dict):
            continue

        for mapping in mappings.values():
            if not isinstance(mapping, dict):
                continue

            arguments = mapping.get("arguments", {})
            if not isinstance(arguments, dict):
                continue

            raw_wavelengths = arguments.get("wavelengths")
            if isinstance(raw_wavelengths, list | tuple):
                for v in raw_wavelengths:
                    process_value(v)

            raw_range = arguments.get("wavelength_range")
            if isinstance(raw_range, list | tuple) and len(raw_range) == 2:
                for v in raw_range:
                    process_value(v)

    return values
