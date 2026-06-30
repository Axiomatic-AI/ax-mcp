"""Unit tests for model_fitter local-data inlining."""

import json
from typing import ClassVar
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from axiomatic_mcp.servers.modelfitter.data_inlining import (
    DataInliningError,
    build_preamble,
    load_table,
    preview_table,
)
from axiomatic_mcp.servers.modelfitter.services.model_fitter_service import (
    ModelFitterService,
)

_SVC_CLIENT = "axiomatic_mcp.servers.modelfitter.services.model_fitter_service.AxiomaticAPIClient"


def _exec_preamble(preamble: str) -> dict:
    ns: dict = {}
    # exercise the generated preamble exactly as the sandbox does (in-process exec)
    exec(preamble, ns)
    return ns["data"]


class _CaptureClient:
    """Stand-in AxiomaticAPIClient that records the posted code instead of calling the API."""

    captured: ClassVar[dict] = {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def post(self, route, data=None):
        _CaptureClient.captured["code"] = data["code"]
        return {"success": True, "result": {}}


# CSV loads into a DataFrame with the expected columns and values.
def test_load_csv(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("t,y\n0.0,1.0\n1.0,2.5\n")
    df = load_table(str(p))
    assert list(df.columns) == ["t", "y"]
    assert df["y"].tolist() == [1.0, 2.5]


# A records-style JSON array loads into a tabular DataFrame.
def test_load_json_records(tmp_path):
    p = tmp_path / "d.json"
    p.write_text(json.dumps([{"t": 0.0, "y": 1.0}, {"t": 1.0, "y": 2.5}]))
    df = load_table(str(p))
    assert df["t"].tolist() == [0.0, 1.0]


# A nonexistent path is reported clearly.
def test_load_missing_file_raises():
    with pytest.raises(DataInliningError, match="not found"):
        load_table("/no/such/file.csv")


# Unsupported extensions are rejected before any read attempt.
def test_load_unsupported_extension_raises(tmp_path):
    p = tmp_path / "d.parquet"
    p.write_text("x")
    with pytest.raises(DataInliningError, match="Unsupported"):
        load_table(str(p))


# A header-only CSV (no rows) is treated as empty.
def test_load_empty_csv_raises(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("t,y\n")
    with pytest.raises(DataInliningError, match="empty"):
        load_table(str(p))


# The preamble defines `data` as a dict of column -> numpy array.
def test_build_preamble_defines_data_dict():
    df = pd.DataFrame({"t": [0.0, 1.0], "y": [1.0, 2.5]})
    data = _exec_preamble(build_preamble(df))
    assert set(data.keys()) == {"t", "y"}
    assert isinstance(data["t"], np.ndarray)
    assert data["y"].tolist() == [1.0, 2.5]


# Float values round-trip through the literal without precision loss.
def test_build_preamble_preserves_precision():
    df = pd.DataFrame({"x": [0.1234567890123456, 9.876543210987654]})
    data = _exec_preamble(build_preamble(df))
    assert data["x"].tolist() == [0.1234567890123456, 9.876543210987654]


# Explicit columns select only the requested subset.
def test_build_preamble_column_subset():
    df = pd.DataFrame({"t": [0.0], "y": [1.0], "z": [2.0]})
    data = _exec_preamble(build_preamble(df, columns=["t", "z"]))
    assert set(data.keys()) == {"t", "z"}


# An unknown explicit column is reported as not found.
def test_build_preamble_unknown_column_raises():
    df = pd.DataFrame({"t": [0.0]})
    with pytest.raises(DataInliningError, match="not found"):
        build_preamble(df, columns=["nope"])


# A non-numeric column cannot be coerced to float.
def test_build_preamble_non_numeric_raises():
    df = pd.DataFrame({"label": ["a", "b"]})
    with pytest.raises(DataInliningError, match="not numeric"):
        build_preamble(df)


# NaN/inf values are rejected rather than emitted as invalid literals.
def test_build_preamble_non_finite_raises():
    df = pd.DataFrame({"y": [1.0, float("nan")]})
    with pytest.raises(DataInliningError, match="NaN/inf"):
        build_preamble(df)


# A preamble larger than the cap is refused.
def test_build_preamble_size_cap_raises():
    df = pd.DataFrame({"y": [1.0, 2.0, 3.0]})
    with pytest.raises(DataInliningError, match="exceeds"):
        build_preamble(df, max_bytes=10)


# Every bad column is reported in a single error, not one at a time.
def test_build_preamble_aggregates_all_problems():
    df = pd.DataFrame({"t": [1.0], "label": ["a"], "bad": [float("inf")]})
    with pytest.raises(DataInliningError) as exc:
        build_preamble(df)
    msg = str(exc.value)
    assert "label" in msg and "bad" in msg


# preview_table returns column names, dtypes, and a head sample.
def test_preview_table_returns_schema_and_sample(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("t,temp,note\n0.0,1.0,a\n1.0,2.0,b\n2.0,3.0,c\n")
    info = preview_table(str(p), n_rows=2)
    assert info["columns"] == ["t", "temp", "note"]
    assert set(info["dtypes"]) == {"t", "temp", "note"}
    assert info["dtypes"]["note"] == "object"
    assert len(info["sample"]) == 2
    assert info["sample"][0]["t"] == 0.0


# preview_table rejects unsupported extensions like load_table does.
def test_preview_table_unsupported_extension_raises(tmp_path):
    p = tmp_path / "d.parquet"
    p.write_text("x")
    with pytest.raises(DataInliningError, match="Unsupported"):
        preview_table(str(p))


# With a data_file, the service prepends the numpy preamble to the code.
def test_service_prepends_preamble(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("t,y\n0.0,1.0\n1.0,2.5\n")
    _CaptureClient.captured = {}
    with patch(_SVC_CLIENT, _CaptureClient):
        ModelFitterService().execute_code("export('ok', 1)", data_file=str(p))
    code = _CaptureClient.captured["code"]
    assert "import numpy as np" in code
    assert "data = {" in code
    assert "export('ok', 1)" in code


# Without a data_file, the code is sent through unchanged.
def test_service_no_data_file_sends_code_unchanged():
    _CaptureClient.captured = {}
    with patch(_SVC_CLIENT, _CaptureClient):
        ModelFitterService().execute_code("export('ok', 1)")
    assert _CaptureClient.captured["code"] == "export('ok', 1)"
