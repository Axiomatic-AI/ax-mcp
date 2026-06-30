"""Load a local CSV/JSON file and inline it as a numpy-only preamble.

The v2 sandbox runs in-process exec() behind an import whitelist that allows
numpy but NOT pandas/io/json. pandas is used HERE (MCP-side, on the user's
machine) only to read the file; the emitted preamble imports numpy only.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".json"}

# Soft cap on the generated preamble string. Large data is not supported in
# this inline path (see the spec's roadmap: Phase 2/3).
DEFAULT_MAX_PREAMBLE_BYTES = 5 * 1024 * 1024


class DataInliningError(Exception):
    """Raised when a local data file cannot be loaded or inlined."""


def load_table(path: str) -> pd.DataFrame:
    """Load a local .csv or .json file into a DataFrame.

    JSON must be tabular (records list, or {column: [values]}).
    """
    p = Path(path)
    if not p.is_file():
        raise DataInliningError(f"Data file not found: {path}")

    ext = p.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise DataInliningError(f"Unsupported data file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}")

    try:
        df = pd.read_csv(p) if ext == ".csv" else pd.read_json(p)
    except Exception as e:
        raise DataInliningError(f"Failed to read {path}: {e}") from e

    if df.empty:
        raise DataInliningError(f"Data file is empty: {path}")

    return df


def preview_table(path: str, n_rows: int = 20) -> dict:
    """Return a lightweight schema preview: column names, dtypes, and the first
    n_rows as records. CSV reads only the head (nrows); JSON is read in full.
    """
    p = Path(path)
    if not p.is_file():
        raise DataInliningError(f"Data file not found: {path}")

    ext = p.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise DataInliningError(f"Unsupported data file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}")

    try:
        df = pd.read_csv(p, nrows=n_rows) if ext == ".csv" else pd.read_json(p).head(n_rows)
    except Exception as e:
        raise DataInliningError(f"Failed to read {path}: {e}") from e

    return {
        "columns": list(df.columns),
        "dtypes": {c: str(df[c].dtype) for c in df.columns},
        "sample": df.to_dict(orient="records"),
    }


def build_preamble(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    max_bytes: int = DEFAULT_MAX_PREAMBLE_BYTES,
) -> str:
    """Build a numpy-only preamble defining `data` as a dict of
    column-name -> 1-D float np.array.

    Validation is aggregated: every unusable column (missing / non-numeric /
    non-finite) is collected and reported in a single DataInliningError, rather
    than failing one column at a time. Also raises if nothing is selected or the
    preamble exceeds max_bytes.
    """
    selected = list(df.columns) if columns is None else columns
    if not selected:
        raise DataInliningError("No columns selected to inline.")

    problems: list[str] = []
    entries: list[str] = []

    for col in selected:
        if col not in df.columns:
            problems.append(f"'{col}': not found")
            continue
        try:
            values = df[col].astype(float).to_numpy()
        except (ValueError, TypeError):
            problems.append(f"'{col}': not numeric ({df[col].dtype})")
            continue
        if not np.isfinite(values).all():
            problems.append(f"'{col}': contains NaN/inf")
            continue
        literal = ", ".join(repr(float(v)) for v in values)
        entries.append(f"    {col!r}: np.array([{literal}]),")

    if problems:
        raise DataInliningError(
            "Cannot inline column(s): "
            + "; ".join(problems)
            + f". Available columns: {list(df.columns)}. "
            + "Pass `columns=[...]` to inline a usable subset."
        )

    preamble = "import numpy as np\ndata = {\n" + "\n".join(entries) + "\n}\n"

    size = len(preamble.encode("utf-8"))
    if size > max_bytes:
        raise DataInliningError(
            f"Inlined data ({size} bytes) exceeds the {max_bytes}-byte cap for inline execution. "
            f"Reduce rows/columns; large data is not supported in this path yet."
        )
    return preamble
