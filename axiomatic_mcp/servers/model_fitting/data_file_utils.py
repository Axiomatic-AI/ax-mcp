"""Data file utilities for the DT Optimizer MCP server.

This module provides helper functions for loading and transforming tabular data files
into the format required by the Axiomatic API optimization tools.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd


def validate_file_access(file_path: str) -> None:
    """Validate that a file exists and is readable.

    Args:
        file_path: Path to the data file

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file is not readable
        ValueError: If path is invalid
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("File path must be a non-empty string")

    path_obj = Path(file_path)

    if not path_obj.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    if not path_obj.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Cannot read data file: {file_path}")


def load_data_file(file_path: str, file_format: str | None = None) -> pd.DataFrame:
    """Load a data file using pandas with automatic format detection.

    Args:
        file_path: Path to the data file
        file_format: Optional file format specification. If None, auto-detect from extension.
                    Supported: 'csv', 'excel', 'json', 'parquet'

    Returns:
        pandas DataFrame containing the loaded data

    Raises:
        ValueError: If file format is not supported or detection fails
        FileNotFoundError: If file doesn't exist
        Exception: For pandas-specific loading errors
    """
    validate_file_access(file_path)

    path_obj = Path(file_path)

    # Auto-detect format if not specified
    if file_format is None:
        extension = path_obj.suffix.lower()
        format_map = {".csv": "csv", ".xlsx": "excel", ".xls": "excel", ".json": "json", ".parquet": "parquet"}
        file_format = format_map.get(extension)

        if file_format is None:
            raise ValueError(
                f"Cannot auto-detect file format for {file_path}. "
                f"Supported extensions: {list(format_map.keys())}. "
                f"Please specify file_format parameter explicitly."
            )

    # Load data based on format
    try:
        if file_format == "csv":
            df = pd.read_csv(file_path)
        elif file_format == "excel":
            df = pd.read_excel(file_path)
        elif file_format == "json":
            df = pd.read_json(file_path)
        elif file_format == "parquet":
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}. Supported formats: csv, excel, json, parquet")
    except Exception as e:
        raise Exception(f"Error loading {file_format} file {file_path}: {e!s}") from e

    if df.empty:
        raise ValueError(f"Data file is empty: {file_path}")

    return df


def validate_column_mapping(df: pd.DataFrame, input_data: list[dict], output_data: dict) -> None:
    """Validate that the column mapping is valid for the given DataFrame.

    Args:
        df: pandas DataFrame containing the data
        input_data: List of input column mapping dictionaries
        output_data: Output column mapping dictionary

    Raises:
        ValueError: If column mapping is invalid or columns don't exist
    """
    if not isinstance(input_data, list):
        raise ValueError("input_data must be a list")

    if not isinstance(output_data, dict):
        raise ValueError("output_data must be a dictionary")

    # Validate input column mappings
    inputs = input_data
    if not isinstance(inputs, list):
        raise ValueError("input_data must be a list")

    for i, input_spec in enumerate(inputs):
        if not isinstance(input_spec, dict):
            raise ValueError(f"Input mapping {i} must be a dictionary")

        required_keys = {"column", "name", "unit"}
        if not all(key in input_spec for key in required_keys):
            raise ValueError(f"Input mapping {i} must contain keys: {required_keys}. Got: {set(input_spec.keys())}")

        column = input_spec["column"]
        if column not in df.columns:
            raise ValueError(f"Input column '{column}' not found in data file. Available columns: {list(df.columns)}")

    # Validate output column mapping
    output = output_data
    if not isinstance(output, dict):
        raise ValueError("output_data must be a dictionary")

    required_keys = {"name", "unit"}
    if not all(key in output for key in required_keys):
        raise ValueError(f"Output mapping must contain keys: {required_keys}")

    # Check for output column specification - now only supports 'columns' key
    if "columns" not in output:
        raise ValueError("Output mapping must specify 'columns' (either string for single column or list for multiple columns)")

    columns = output["columns"]

    # Handle both single column (string) and multi-column (list) cases
    if isinstance(columns, str):
        # Single column output - convert to list for uniform handling
        columns_list = [columns]
    elif isinstance(columns, list):
        # Multi-column output
        if len(columns) == 0:
            raise ValueError("Output 'columns' list cannot be empty")
        columns_list = columns
    else:
        raise ValueError("Output 'columns' must be either a string (single column) or a list (multiple columns)")

    # Validate all specified columns exist in the DataFrame
    for column in columns_list:
        if column not in df.columns:
            raise ValueError(f"Output column '{column}' not found in data file. Available columns: {list(df.columns)}")


def transform_file_to_optimization_format(df: pd.DataFrame, input_data: list[dict], output_data: dict) -> tuple[list[dict], dict]:
    """Transform DataFrame data into the format expected by optimization tools.

    Args:
        df: pandas DataFrame containing the loaded data
        input_data: List of input column mapping dictionaries
        output_data: Output column mapping dictionary

    Returns:
        Tuple of (input_data, output_data) in the format expected by optimization tools:
        - input_data: List of dicts with 'name', 'unit', 'magnitudes' keys
        - output_data: Dict with 'name', 'unit', 'magnitudes' keys

    Raises:
        ValueError: If data transformation fails
    """
    validate_column_mapping(df, input_data, output_data)

    # Transform input data
    transformed_input_data = []
    for input_spec in input_data:
        column = input_spec["column"]

        # Check for missing values
        if df[column].isnull().any():
            raise ValueError(f"Input column '{column}' contains missing values. Please clean the data before optimization.")

        # Convert to list, handling various pandas dtypes
        try:
            magnitudes = df[column].astype(float).tolist()
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert input column '{column}' to numeric values: {e!s}") from e

        transformed_input_data.append({"name": input_spec["name"], "unit": input_spec["unit"], "magnitudes": magnitudes})

    # Transform output data - now unified under 'columns' key
    output_spec = output_data
    columns = output_spec["columns"]

    # Handle both single column (string) and multi-column (list) cases
    if isinstance(columns, str):
        # Single column output
        column = columns

        if df[column].isnull().any():
            raise ValueError(f"Output column '{column}' contains missing values. Please clean the data before optimization.")

        try:
            magnitudes = df[column].astype(float).tolist()
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert output column '{column}' to numeric values: {e!s}") from e
    else:
        # Multi-column output (list)
        if len(columns) == 1:
            # Single column specified as list - return flat list
            column = columns[0]

            if df[column].isnull().any():
                raise ValueError(f"Output column '{column}' contains missing values. Please clean the data before optimization.")

            try:
                magnitudes = df[column].astype(float).tolist()
            except (ValueError, TypeError) as e:
                raise ValueError(f"Cannot convert output column '{column}' to numeric values: {e!s}") from e
        else:
            # True multi-column output - return list of lists
            output_arrays = []

            for column in columns:
                if df[column].isnull().any():
                    raise ValueError(f"Output column '{column}' contains missing values. Please clean the data before optimization.")

                try:
                    col_data = df[column].astype(float).values
                    output_arrays.append(col_data)
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Cannot convert output column '{column}' to numeric values: {e!s}") from e

            # Horizontally concatenate arrays and convert to list of lists
            combined_array = np.column_stack(output_arrays)
            magnitudes = combined_array.tolist()

    transformed_output_data = {"name": output_spec["name"], "unit": output_spec["unit"], "magnitudes": magnitudes}

    return transformed_input_data, transformed_output_data


def resolve_output_data_only(data_file: str, output_data: dict, file_format: str | None = None) -> list:
    """Resolve output data from file-based input only.

    This is a simplified version for tools that only need output data (like calculate_r_squared).

    Args:
        data_file: Path to data file
        output_data: Output column mapping dictionary
        file_format: Optional file format

    Returns:
        Output magnitudes in the format expected by calculation functions

    Raises:
        ValueError: If file or mapping is invalid
    """
    # Use file-based approach only
    df = load_data_file(data_file, file_format)

    # Validate the output data specification
    output_spec = output_data
    if not isinstance(output_spec, dict):
        raise ValueError("output_data must be a dictionary")

    required_keys = {"name", "unit"}
    if not all(key in output_spec for key in required_keys):
        raise ValueError(f"Output mapping must contain keys: {required_keys}")

    # Check for output column specification - now only supports 'columns' key
    if "columns" not in output_spec:
        raise ValueError("Output mapping must specify 'columns' (either string for single column or list for multiple columns)")

    # Handle unified 'columns' key (string or list)
    columns = output_spec["columns"]

    if isinstance(columns, str):
        # Single column output
        column = columns
        if column not in df.columns:
            raise ValueError(f"Output column '{column}' not found in data file. Available columns: {list(df.columns)}")

        if df[column].isnull().any():
            raise ValueError(f"Output column '{column}' contains missing values. Please clean the data before calculation.")

        try:
            magnitudes = df[column].astype(float).tolist()
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert output column '{column}' to numeric values: {e!s}") from e
    else:
        # Multi-column output (list)
        if not isinstance(columns, list) or len(columns) == 0:
            raise ValueError("Output 'columns' must be a non-empty list")

        if len(columns) == 1:
            # Single column specified as list - return flat list
            column = columns[0]
            if column not in df.columns:
                raise ValueError(f"Output column '{column}' not found in data file. Available columns: {list(df.columns)}")

            if df[column].isnull().any():
                raise ValueError(f"Output column '{column}' contains missing values. Please clean the data before calculation.")

            try:
                magnitudes = df[column].astype(float).tolist()
            except (ValueError, TypeError) as e:
                raise ValueError(f"Cannot convert output column '{column}' to numeric values: {e!s}") from e
        else:
            # True multi-column output - return list of lists
            output_arrays = []
            for column in columns:
                if column not in df.columns:
                    raise ValueError(f"Output column '{column}' not found in data file. Available columns: {list(df.columns)}")

                if df[column].isnull().any():
                    raise ValueError(f"Output column '{column}' contains missing values. Please clean the data before calculation.")

                try:
                    col_data = df[column].astype(float).values
                    output_arrays.append(col_data)
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Cannot convert output column '{column}' to numeric values: {e!s}") from e

            # Horizontally concatenate arrays and convert to list of lists
            combined_array = np.column_stack(output_arrays)
            magnitudes = combined_array.tolist()

    return magnitudes


def resolve_data_input(data_file: str, input_data: list[dict], output_data: dict, file_format: str | None = None) -> tuple[list[dict], dict]:
    """Resolve data input from file-based input only.

    This function loads data from files and transforms it into the format
    expected by optimization tools.

    Args:
        data_file: Path to data file
        input_data: Input column mapping list
        output_data: Output column mapping dictionary
        file_format: Optional file format

    Returns:
        Tuple of (input_data, output_data) in optimization format

    Raises:
        ValueError: If file or mapping is invalid
    """
    # Use file-based approach only
    df = load_data_file(data_file, file_format)
    return transform_file_to_optimization_format(df, input_data, output_data)
