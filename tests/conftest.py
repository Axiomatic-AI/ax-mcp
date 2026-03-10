from dotenv import load_dotenv
import pytest
load_dotenv()


@pytest.fixture
def simple_request_body_parameter_covariance():
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

@pytest.fixture
def linear_request_body_parameter_covariance():
    return {
    "parameters": [
        {
        "name": "a",
        "value": {
            "magnitude": 2,
            "unit": "dimensionless"
        }
        },
        {
        "name": "b",
        "value": {
            "magnitude": 1,
            "unit": "dimensionless"
        }
        }
    ],
    "bounds": [
        {
        "name": "a",
        "lower": {
            "magnitude": -10,
            "unit": "dimensionless"
        },
        "upper": {
            "magnitude": 10,
            "unit": "dimensionless"
        }
        },
        {
        "name": "b",
        "lower": {
            "magnitude": -10,
            "unit": "dimensionless"
        },
        "upper": {
            "magnitude": 10,
            "unit": "dimensionless"
        }
        },
        {
        "name": "x",
        "lower": {
            "magnitude": -10,
            "unit": "dimensionless"
        },
        "upper": {
            "magnitude": 10,
            "unit": "dimensionless"
        }
        },
        {
        "name": "y",
        "lower": {
            "magnitude": -50,
            "unit": "dimensionless"
        },
        "upper": {
            "magnitude": 50,
            "unit": "dimensionless"
        }
        }
    ],
    "constants": [],
    "input": {
        "name": "x",
        "unit": "dimensionless",
        "magnitudes": [
        1,
        2,
        3,
        4,
        5
        ]
    },
    "target": {
        "name": "y",
        "unit": "dimensionless",
        "magnitudes": [
        4,
        4,
        8,
        8,
        12
        ]
    },
    "function_source": "def linear_model(a: float, b: float, x: float) -> float:\n    return a * x + b",
    "function_name": "linear_model",
    "model_name": "LinearModel",
    "docstring": "Linear model: y = a*x + b",
    "jit_compile": "true",
    "cost_function_type": "mse",
    "scale_params": "false",
    "variance": 1
    }

@pytest.fixture
def nonlinear_request_body_parameter_covariance():
    return {
    "parameters": [
        {
        "name": "amplitude",
        "value": {
            "magnitude": 1,
            "unit": "dimensionless"
        }
        },
        {
        "name": "decay_rate",
        "value": {
            "magnitude": 0.5,
            "unit": "dimensionless"
        }
        },
        {
        "name": "offset",
        "value": {
            "magnitude": 0.1,
            "unit": "dimensionless"
        }
        }
    ],
    "bounds": [
        {
        "name": "amplitude",
        "lower": {
            "magnitude": 0.1,
            "unit": "dimensionless"
        },
        "upper": {
            "magnitude": 5,
            "unit": "dimensionless"
        }
        },
        {
        "name": "decay_rate",
        "lower": {
            "magnitude": 0.01,
            "unit": "dimensionless"
        },
        "upper": {
            "magnitude": 2,
            "unit": "dimensionless"
        }
        },
        {
        "name": "offset",
        "lower": {
            "magnitude": -1,
            "unit": "dimensionless"
        },
        "upper": {
            "magnitude": 1,
            "unit": "dimensionless"
        }
        },
        {
        "name": "t",
        "lower": {
            "magnitude": 0,
            "unit": "dimensionless"
        },
        "upper": {
            "magnitude": 10,
            "unit": "dimensionless"
        }
        },
        {
        "name": "y",
        "lower": {
            "magnitude": -5,
            "unit": "dimensionless"
        },
        "upper": {
            "magnitude": 5,
            "unit": "dimensionless"
        }
        }
    ],
    "constants": [],
    "input": {
        "name": "t",
        "unit": "dimensionless",
        "magnitudes": [
        0,
        0.5,
        1,
        1.5,
        2,
        2.5,
        3,
        3.5,
        4,
        4.5
        ]
    },
    "target": {
        "name": "y",
        "unit": "dimensionless",
        "magnitudes": [
        1.12,
        0.89,
        0.71,
        0.58,
        0.47,
        0.39,
        0.32,
        0.27,
        0.22,
        0.19
        ]
    },
    "function_source": "def exponential_decay(amplitude: float, decay_rate: float, offset: float, t: float) -> float:\n    import jax.numpy as jnp\n    return amplitude * jnp.exp(-decay_rate * t) + offset",
    "function_name": "exponential_decay",
    "model_name": "ExponentialDecayModel",
    "docstring": "Exponential decay: y = amplitude * exp(-decay_rate * t) + offset",
    "jit_compile": "true",
    "cost_function_type": "mse",
    "scale_params": "false",
    "variance": 0.01
    }

@pytest.fixture
def invalid_request_body_parameter_covariance():
    return {
        "invalid": "data"
    }

@pytest.fixture
def simple_response_parameter_covariance():
    return {
        "param_names": [
            "a"
        ],
        "covariance_matrix": [
            [
                0.01
            ]
        ],
        "scale_params": "false"
    }

@pytest.fixture
def linear_response_parameter_covariance():
    {
    "param_names": [
        "a",
        "b"
    ],
    "sandwich_covariance": [
        [
        0.09999950000221229,
        -0.29999820000798677
        ],
        [
        -0.29999820000798677,
        1.0999935000288352
        ]
    ],
    "inverse_hessian_covariance": [
        [
        0.09999975000073741,
        -0.2999991000026622
        ],
        [
        -0.29999910000266217,
        1.0999967500096115
        ]
    ],
    "scale_params": "false"
    }

def nonlinear_response_parameter_covariance():
    return {
    "param_names": [
        "amplitude",
        "decay_rate",
        "offset"
    ],
    "sandwich_covariance": [
        [
        0.00029701918918092086,
        -0.00011370038422729057,
        -0.0001957595163521092
        ],
        [
        -0.00011370038422729068,
        0.0004935784860346853,
        0.0003724357503380737
        ],
        [
        -0.00019575951635210934,
        0.00037243575033807353,
        0.0003303280343258498
        ]
    ],
    "inverse_hessian_covariance": [
        [
        0.020539122953990307,
        -0.016305197141040475,
        -0.017409060317235752
        ],
        [
        -0.016305197141040475,
        0.03292032352036665,
        0.024706905339776902
        ],
        [
        -0.017409060317235752,
        0.024706905339776902,
        0.021688880975936978
        ]
    ],
    "scale_params": "false"
    }