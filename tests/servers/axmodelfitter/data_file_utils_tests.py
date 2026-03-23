"""Tests for axmodelfitter/data_file_utils.py"""

import json

import pandas as pd
import pytest

from axiomatic_mcp.servers.axmodelfitter.data_file_utils import (
    load_data_file,
    resolve_data_input,
    resolve_output_data_only,
    transform_file_to_optimization_format,
    validate_column_mapping,
    validate_file_access,
)

def test_validate_file_access_empty_string_raises():
    with pytest.raises(ValueError, match="non-empty string"):
        validate_file_access("")


def test_validate_file_access_non_string_raises():
    with pytest.raises(ValueError):
        validate_file_access(None)


def test_validate_file_access_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        validate_file_access("/nonexistent/path/file.csv")


def test_validate_file_access_directory_raises(tmp_path):
    with pytest.raises(ValueError, match="not a file"):
        validate_file_access(str(tmp_path))


def test_validate_file_access_valid_file_passes(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("a,b\n1,2\n")
    validate_file_access(str(f))  # should not raise


def test_load_data_file_csv_auto_detect(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("a,b\n1,2\n3,4\n")
    df = load_data_file(str(f))
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2


def test_load_data_file_json_auto_detect(tmp_path):
    f = tmp_path / "data.json"
    f.write_text(json.dumps([{"a": 1, "b": 2}, {"a": 3, "b": 4}]))
    df = load_data_file(str(f))
    assert list(df.columns) == ["a", "b"]


def test_load_data_file_explicit_format_overrides_extension(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("a,b\n1,2\n3,4\n")
    df = load_data_file(str(f), file_format="csv")
    assert list(df.columns) == ["a", "b"]


def test_load_data_file_unknown_extension_raises(tmp_path):
    f = tmp_path / "data.xyz"
    f.write_text("a,b\n1,2\n")
    with pytest.raises(ValueError, match="Cannot auto-detect"):
        load_data_file(str(f))


def test_load_data_file_unsupported_format_raises(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("a,b\n1,2\n")
    with pytest.raises(Exception, match="Unsupported file format"):
        load_data_file(str(f), file_format="xml")


def test_load_data_file_empty_raises(tmp_path):
    f = tmp_path / "empty.csv"
    f.write_text("a,b\n")  # header only → empty DataFrame
    with pytest.raises(ValueError, match="empty"):
        load_data_file(str(f))


def test_load_data_file_nonexistent_raises():
    with pytest.raises(FileNotFoundError):
        load_data_file("/no/such/file.csv")


def test_validate_column_mapping_input_not_list_raises(simple_df, simple_output_data):
    with pytest.raises(ValueError, match="input_data must be a list"):
        validate_column_mapping(simple_df, "not_a_list", simple_output_data)


def test_validate_column_mapping_output_not_dict_raises(simple_df, simple_input_data):
    with pytest.raises(ValueError, match="output_data must be a dictionary"):
        validate_column_mapping(simple_df, simple_input_data, "not_a_dict")


def test_validate_column_mapping_input_spec_not_dict_raises(simple_df, simple_output_data):
    with pytest.raises(ValueError, match="must be a dictionary"):
        validate_column_mapping(simple_df, ["not_a_dict"], simple_output_data)


def test_validate_column_mapping_input_spec_missing_key_raises(simple_df, simple_output_data):
    bad_input = [{"column": "x", "name": "X"}]  # missing 'unit'
    with pytest.raises(ValueError, match="must contain keys"):
        validate_column_mapping(simple_df, bad_input, simple_output_data)


def test_validate_column_mapping_input_column_missing_raises(simple_df, simple_output_data):
    bad_input = [{"column": "missing", "name": "X", "unit": "m"}]
    with pytest.raises(ValueError, match="not found in data file"):
        validate_column_mapping(simple_df, bad_input, simple_output_data)


def test_validate_column_mapping_output_missing_name_raises(simple_df, simple_input_data):
    with pytest.raises(ValueError, match="must contain keys"):
        validate_column_mapping(simple_df, simple_input_data, {"unit": "s", "columns": "y"})


def test_validate_column_mapping_output_missing_columns_key_raises(simple_df, simple_input_data):
    with pytest.raises(ValueError, match="must specify 'columns'"):
        validate_column_mapping(simple_df, simple_input_data, {"name": "Y", "unit": "s"})


def test_validate_column_mapping_output_empty_list_raises(simple_df, simple_input_data):
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_column_mapping(simple_df, simple_input_data, {"name": "Y", "unit": "s", "columns": []})


def test_validate_column_mapping_output_column_missing_raises(simple_df, simple_input_data):
    with pytest.raises(ValueError, match="not found in data file"):
        validate_column_mapping(simple_df, simple_input_data, {"name": "Y", "unit": "s", "columns": "missing"})


def test_validate_column_mapping_output_columns_invalid_type_raises(simple_df, simple_input_data):
    with pytest.raises(ValueError, match="must be either a string"):
        validate_column_mapping(simple_df, simple_input_data, {"name": "Y", "unit": "s", "columns": 42})


def test_validate_column_mapping_string_column_passes(simple_df, simple_input_data, simple_output_data):
    validate_column_mapping(simple_df, simple_input_data, simple_output_data)


def test_validate_column_mapping_list_column_passes(simple_df, simple_input_data):
    validate_column_mapping(simple_df, simple_input_data, {"name": "Y", "unit": "s", "columns": ["y"]})


def test_validate_column_mapping_multi_column_list_passes(simple_df, simple_input_data):
    validate_column_mapping(simple_df, simple_input_data, {"name": "Y", "unit": "s", "columns": ["y", "z"]})


def test_validate_column_mapping_two_inputs_one_output_passes(two_input_df, two_input_data, one_output_data):
    validate_column_mapping(two_input_df, two_input_data, one_output_data)


def test_validate_column_mapping_two_inputs_second_missing_raises(two_input_df, one_output_data):
    bad_inputs = [
        {"column": "a", "name": "A", "unit": "m"},
        {"column": "missing", "name": "B", "unit": "kg"},
    ]
    with pytest.raises(ValueError, match="not found in data file"):
        validate_column_mapping(two_input_df, bad_inputs, one_output_data)


# ---------------------------------------------------------------------------
# transform_file_to_optimization_format
# ---------------------------------------------------------------------------

def test_transform_single_input_string_output(simple_df, simple_input_data, simple_output_data):
    inputs, output = transform_file_to_optimization_format(simple_df, simple_input_data, simple_output_data)
    assert inputs == [{"name": "X", "unit": "m", "magnitudes": [1.0, 2.0, 3.0]}]
    assert output == {"name": "Y", "unit": "s", "magnitudes": [4.0, 5.0, 6.0]}


def test_transform_list_of_one_output_is_flat(simple_df, simple_input_data):
    _, output = transform_file_to_optimization_format(
        simple_df, simple_input_data, {"name": "Y", "unit": "s", "columns": ["y"]}
    )
    assert output["magnitudes"] == [4.0, 5.0, 6.0]


def test_transform_multi_column_output_is_list_of_lists(simple_df, simple_input_data):
    _, output = transform_file_to_optimization_format(
        simple_df, simple_input_data, {"name": "Y", "unit": "s", "columns": ["y", "z"]}
    )
    assert output["magnitudes"] == [[4.0, 7.0], [5.0, 8.0], [6.0, 9.0]]


def test_transform_two_inputs_one_output(two_input_df, two_input_data, one_output_data):
    inputs, output = transform_file_to_optimization_format(two_input_df, two_input_data, one_output_data)
    assert len(inputs) == 2
    assert inputs[0] == {"name": "A", "unit": "m", "magnitudes": [1.0, 2.0, 3.0]}
    assert inputs[1] == {"name": "B", "unit": "kg", "magnitudes": [10.0, 20.0, 30.0]}
    assert output == {"name": "C", "unit": "N", "magnitudes": [100.0, 200.0, 300.0]}


def test_transform_input_null_raises(simple_input_data, simple_output_data):
    df = pd.DataFrame({"x": [1.0, None, 3.0], "y": [4.0, 5.0, 6.0]})
    with pytest.raises(ValueError, match="missing values"):
        transform_file_to_optimization_format(df, simple_input_data, simple_output_data)


def test_transform_output_null_raises(simple_input_data, simple_output_data):
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [4.0, None, 6.0]})
    with pytest.raises(ValueError, match="missing values"):
        transform_file_to_optimization_format(df, simple_input_data, simple_output_data)


def test_transform_non_numeric_input_raises(simple_input_data, simple_output_data):
    df = pd.DataFrame({"x": ["a", "b", "c"], "y": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError, match="numeric"):
        transform_file_to_optimization_format(df, simple_input_data, simple_output_data)


def test_transform_non_numeric_output_raises(simple_input_data, simple_output_data):
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": ["a", "b", "c"]})
    with pytest.raises(ValueError, match="numeric"):
        transform_file_to_optimization_format(df, simple_input_data, simple_output_data)


def test_resolve_output_string_column(csv_file, simple_output_data):
    result = resolve_output_data_only(csv_file, simple_output_data)
    assert result == [4.0, 5.0, 6.0]


def test_resolve_output_list_of_one_is_flat(csv_file):
    result = resolve_output_data_only(csv_file, {"name": "Y", "unit": "s", "columns": ["y"]})
    assert result == [4.0, 5.0, 6.0]


def test_resolve_output_multi_column_is_list_of_lists(csv_file):
    result = resolve_output_data_only(csv_file, {"name": "Y", "unit": "s", "columns": ["y", "z"]})
    assert result == [[4.0, 7.0], [5.0, 8.0], [6.0, 9.0]]


def test_resolve_output_missing_column_raises(csv_file):
    with pytest.raises(ValueError, match="not found"):
        resolve_output_data_only(csv_file, {"name": "Y", "unit": "s", "columns": "missing"})


def test_resolve_output_null_column_raises(tmp_path):
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "y": [4.0, None, 6.0]})
    f = tmp_path / "data.csv"
    df.to_csv(f, index=False)
    with pytest.raises(ValueError, match="missing values"):
        resolve_output_data_only(str(f), {"name": "Y", "unit": "s", "columns": "y"})


def test_resolve_output_missing_columns_key_raises(csv_file):
    with pytest.raises(ValueError, match="must specify 'columns'"):
        resolve_output_data_only(csv_file, {"name": "Y", "unit": "s"})


def test_resolve_output_empty_columns_list_raises(csv_file):
    with pytest.raises(ValueError, match="non-empty list"):
        resolve_output_data_only(csv_file, {"name": "Y", "unit": "s", "columns": []})
        

def test_resolve_data_input_basic_csv(csv_file, simple_input_data, simple_output_data):
    inputs, output = resolve_data_input(csv_file, simple_input_data, simple_output_data)
    assert inputs == [{"name": "X", "unit": "m", "magnitudes": [1.0, 2.0, 3.0]}]
    assert output == {"name": "Y", "unit": "s", "magnitudes": [4.0, 5.0, 6.0]}


def test_resolve_data_input_explicit_format(tmp_path, simple_df, simple_input_data, simple_output_data):
    f = tmp_path / "data.txt"
    simple_df.to_csv(f, index=False)
    inputs, _ = resolve_data_input(str(f), simple_input_data, simple_output_data, file_format="csv")
    assert inputs[0]["magnitudes"] == [1.0, 2.0, 3.0]


def test_resolve_data_input_missing_file_raises(simple_input_data, simple_output_data):
    with pytest.raises(FileNotFoundError):
        resolve_data_input("/no/file.csv", simple_input_data, simple_output_data)
