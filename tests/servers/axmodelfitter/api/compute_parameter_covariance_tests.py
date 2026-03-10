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

# TODO Why does the request body need to contain lowercase false for json? Didn't feel like tracing the object back all the way. 
def test_compute_parameter_covariance_valid_request(client, endpoint, simple_request_body_parameter_covariance):
    response = client.post(endpoint, simple_request_body_parameter_covariance)
    assert "sandwich_covariance" in response.keys()
    assert isinstance(response["sandwich_covariance"], list)
    assert "inverse_hessian_covariance" in response.keys()
    assert isinstance(response["inverse_hessian_covariance"], list)
    assert "a" in response["param_names"]
    assert "scale_params" in response.keys()

def test_compute_parameter_covariance_invalid_request(client, endpoint):
    with pytest.raises(httpx.HTTPStatusError):
        client.post(endpoint, {"invalid": "data"})
