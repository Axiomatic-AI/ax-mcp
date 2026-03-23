"""Tests for the ax-api /digital-twin/compute_parameter_covariance endpoint."""

import httpx
import pytest
from axiomatic_mcp.shared import AxiomaticAPIClient
from axiomatic_mcp.servers.axmodelfitter.services.covariance_service import CovarianceService

@pytest.fixture
def covariance_service():
    """Fixture for CovarianceService instance."""
    return CovarianceService()

@pytest.fixture
def endpoint():
    return "/digital-twin/compute-parameter-covariance"

# TODO Why does the request body need to contain lowercase false for json? Didn't feel like tracing the object back all the way.
@pytest.mark.integration
def test_compute_parameter_covariance_valid_request(endpoint, simple_request_body_parameter_covariance):
    with AxiomaticAPIClient() as client:
        response = client.post(endpoint, simple_request_body_parameter_covariance)
    assert "sandwich_covariance" in response.keys()
    assert isinstance(response["sandwich_covariance"], list)
    assert "inverse_hessian_covariance" in response.keys()
    assert isinstance(response["inverse_hessian_covariance"], list)
    assert "a" in response["param_names"]
    assert "scale_params" in response.keys()


@pytest.mark.integration
def test_compute_parameter_covariance_invalid_request(endpoint):
    with pytest.raises(httpx.HTTPStatusError):
        with AxiomaticAPIClient() as client:
            client.post(endpoint, {"invalid": "data"})


@pytest.mark.asyncio
@pytest.mark.integration
async def test_covariance_service(covariance_service, nonlinear_request_body_parameter_covariance):
    """Ensure a valid request is successful."""
    result = await covariance_service.compute_covariance(nonlinear_request_body_parameter_covariance)
    assert result["success"] == True