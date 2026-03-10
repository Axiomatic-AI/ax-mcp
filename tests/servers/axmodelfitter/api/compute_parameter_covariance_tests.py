"""Tests for the ax-api /digital-twin/compute_parameter_covariance endpoint."""

import json
import httpx
import requests
import pytest
from axiomatic_mcp.shared import AxiomaticAPIClient

@pytest.fixture
def endpoint():
    return "/digital-twin/compute-parameter-covariance"

@pytest.fixture
def client():
    return AxiomaticAPIClient()

@pytest.fixture
def valid_request_body():
    """Return a valid request -> Used to ensure request body is unchanged on the ax-stack side."""
    return {
        "parameters": [
            {"name": "a", "value": {"magnitude": 2.0, "unit": "dimensionless"}},
        ],
        "bounds": [
            {
                "name": "a",
                "lower": {"magnitude": 0.0, "unit": "dimensionless"},
                "upper": {"magnitude": 5.0, "unit": "dimensionless"},
            },
            {
                "name": "x",
                "lower": {"magnitude": -10.0, "unit": "dimensionless"},
                "upper": {"magnitude": 10.0, "unit": "dimensionless"},
            },
            {
                "name": "y",
                "lower": {"magnitude": -50.0, "unit": "dimensionless"},
                "upper": {"magnitude": 50.0, "unit": "dimensionless"},
            },
        ],
        "constants": [],
        "input": {"name": "x", "unit": "dimensionless", "magnitudes": [0.5, 1.0]},
        "target": {"name": "y", "unit": "dimensionless", "magnitudes": [1.0, 2.0]},
        "function_source": "def f(a: float, x: float) -> float:\n    return a * x",
        "function_name": "f",
        "model_name": "LinearModel",
        "docstring": "",
        "jit_compile": "false",
        "cost_function_type": "mse",
        "scale_params": "false",
        "variance": 0.01,
    }

# TODO Why does the request body need to 
def test_compute_parameter_covariance_valid_request(client, endpoint, valid_request_body):
    print(valid_request_body)
    response = client.post(endpoint, valid_request_body)
    assert "sandwich_covariance" in response.keys()
    assert isinstance(response["sandwich_covariance"], list)
    assert "inverse_hessian_covariance" in response.keys()
    assert isinstance(response["inverse_hessian_covariance"], list)
    assert "a" in response["param_names"]

def test_compute_parameter_covariance_invalid_request(client, endpoint):
    with pytest.raises(httpx.HTTPStatusError):
        client.post(endpoint, {"invalid": "data"})
