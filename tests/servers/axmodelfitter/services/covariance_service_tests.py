"""Tests for axmodelfitter/services/covariance_service.py"""

import pytest
import pytest_asyncio

from axiomatic_mcp.servers.axmodelfitter.services.covariance_service import CovarianceService

@pytest.fixture
def covariance_service():
    """Fixture for CovarianceService instance."""
    return CovarianceService()

@pytest.fixture
def valid_covariance_matrix():
    """Return a valid covariance matrix for testing."""
    return [[0.1, 0.01], [0.01, 0.2]]

@pytest.fixture
def invalid_covariance_matrix_non_square():
    """Return a non-square covariance matrix."""
    return [[0.1, 0.01, 0.02], [0.01, 0.2, 0.03]]

@pytest.fixture
def invalid_covariance_matrix_non_symmetric():
    """Return a non-symmetric covariance matrix."""
    return [[0.1, 0.01], [0.02, 0.2]]

@pytest.fixture
def invalid_covariance_matrix_non_positive_definite():
    """Return a covariance matrix that is not positive definite."""
    return [[-0.1, 0.01], [0.01, -0.2]]

@pytest.mark.asyncio
async def test_covariance_service(covariance_service, nonlinear_request_body_parameter_covariance):
    """Ensure a valid request is successful."""
    result = await covariance_service.compute_covariance(nonlinear_request_body_parameter_covariance)
    assert result["success"] == True
    
def test_has_valid_covariance(covariance_service, valid_covariance_matrix, invalid_covariance_matrix_non_square, invalid_covariance_matrix_non_symmetric, invalid_covariance_matrix_non_positive_definite):
    assert covariance_service._has_valid_covariance({"sandwich_covariance": valid_covariance_matrix, "inverse_hessian_covariance": None}) == True

    assert covariance_service._has_valid_covariance({"sandwich_covariance": invalid_covariance_matrix_non_square, "inverse_hessian_covariance": None}) == False
    assert covariance_service._has_valid_covariance({"sandwich_covariance": invalid_covariance_matrix_non_symmetric, "inverse_hessian_covariance": None}) == False
    assert covariance_service._has_valid_covariance({"sandwich_covariance": invalid_covariance_matrix_non_positive_definite, "inverse_hessian_covariance": None}) == False

    assert covariance_service._has_valid_covariance({"sandwich_covariance": None, "inverse_hessian_covariance": valid_covariance_matrix}) == True

    assert covariance_service._has_valid_covariance({"sandwich_covariance": None, "inverse_hessian_covariance": invalid_covariance_matrix_non_square}) == False
    assert covariance_service._has_valid_covariance({"sandwich_covariance": None, "inverse_hessian_covariance": invalid_covariance_matrix_non_symmetric}) == False
    assert covariance_service._has_valid_covariance({"sandwich_covariance": None, "inverse_hessian_covariance": invalid_covariance_matrix_non_positive_definite}) == False