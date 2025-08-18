import re

UNIT_CONVERSIONS = {
    "nm": 1e-3,
    "um": 1.0,
    "mm": 1e3,
    "m": 1e6,
}


def str_units_to_um(str_units: str) -> float:
    """
    Convert wavelength string with units into micrometers (um).
    Supported units: nm, um, mm, m
    """

    match = re.match(r"^([\d.]+)\s*([a-zA-Z]+)$", str_units)
    if not match:
        raise ValueError(f"Invalid wavelength specification: '{str_units}'")

    numeric_value = float(match.group(1))
    unit = match.group(2)

    if unit not in UNIT_CONVERSIONS:
        raise ValueError(f"Unsupported unit: '{unit}'")

    return numeric_value * UNIT_CONVERSIONS[unit]


def get_linear_range(min_value: float, max_value: float, num_points: int = 10000) -> list[float]:
    """
    Generate a linear range between min and max with num_points points.
    Values are rounded to 6 decimal places.
    """
    if num_points < 2:
        return [round(min_value, 6)]

    step = (max_value - min_value) / (num_points - 1)
    return [round(min_value + i * step, 6) for i in range(num_points)]
