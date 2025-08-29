import re


def str_units_to_um(str_units: str) -> float:
    """
    Convert wavelength string with units into micrometers (um).
    Supported units: nm, um, mm, m
    """
    unit_conversions = {
        "nm": 1e-3,
        "um": 1.0,
        "mm": 1e3,
        "m": 1e6,
    }

    match = re.match(r"^([\d.]+)\s*([a-zA-Z]+)$", str_units)
    if not match:
        raise ValueError(f"Invalid wavelength specification: '{str_units}'")

    numeric_value = float(match.group(1))
    unit = match.group(2)

    if unit not in unit_conversions:
        raise ValueError(f"Unsupported unit: '{unit}'")

    return numeric_value * unit_conversions[unit]


def get_linear_range(min: float, max: float, num_points: int) -> list[float]:
    """
    Generate a linear range between min and max with num_points points.
    Values are rounded to 6 decimal places.
    """
    if num_points < 2:
        return [round(min, 6)]

    step = (max - min) / (num_points - 1)
    return [round(min + i * step, 6) for i in range(num_points)]
