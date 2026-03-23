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
    
def test_has_valid_covariance(covariance_service, valid_covariance_matrix, invalid_covariance_matrix_non_square, invalid_covariance_matrix_non_symmetric, invalid_covariance_matrix_non_positive_definite):
    assert covariance_service._has_valid_covariance({"sandwich_covariance": valid_covariance_matrix, "inverse_hessian_covariance": None}) == True

def test_has_valid_covariance_invalid_non_square(covariance_service, invalid_covariance_matrix_non_square):
    assert covariance_service._has_valid_covariance({"sandwich_covariance": invalid_covariance_matrix_non_square, "inverse_hessian_covariance": None}) == False

def test_has_valid_covariance_invalid_non_symmetric(covariance_service, invalid_covariance_matrix_non_symmetric):
    assert covariance_service._has_valid_covariance({"sandwich_covariance": invalid_covariance_matrix_non_symmetric, "inverse_hessian_covariance": None}) == False

def test_has_valid_covariance_invalid_non_positive_definite(covariance_service, invalid_covariance_matrix_non_positive_definite):
    assert covariance_service._has_valid_covariance({"sandwich_covariance": invalid_covariance_matrix_non_positive_definite, "inverse_hessian_covariance": None}) == False

def test_has_valid_covariance_with_inverse_hessian(covariance_service, valid_covariance_matrix, invalid_covariance_matrix_non_square, invalid_covariance_matrix_non_symmetric, invalid_covariance_matrix_non_positive_definite):
    assert covariance_service._has_valid_covariance({"sandwich_covariance": None, "inverse_hessian_covariance": valid_covariance_matrix}) == True

def test_has_valid_covariance_invalid_inverse_hessian_non_square(covariance_service, invalid_covariance_matrix_non_square):
    assert covariance_service._has_valid_covariance({"sandwich_covariance": None, "inverse_hessian_covariance": invalid_covariance_matrix_non_square}) == False

def test_has_valid_covariance_invalid_inverse_hessian_non_symmetric(covariance_service, invalid_covariance_matrix_non_symmetric):
    assert covariance_service._has_valid_covariance({"sandwich_covariance": None, "inverse_hessian_covariance": invalid_covariance_matrix_non_symmetric}) == False
    
def test_has_valid_covariance_invalid_inverse_hessian_non_positive_definite(covariance_service, invalid_covariance_matrix_non_positive_definite):
    assert covariance_service._has_valid_covariance({"sandwich_covariance": None, "inverse_hessian_covariance": invalid_covariance_matrix_non_positive_definite}) == False

def test_has_valid_covariance_empty(covariance_service):
    assert covariance_service._has_valid_covariance({"sandwich_covariance": None, "inverse_hessian_covariance": None}) == False