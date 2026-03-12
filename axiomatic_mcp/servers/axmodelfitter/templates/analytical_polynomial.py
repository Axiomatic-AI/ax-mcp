SOURCE = """def y(x, a, b, c):
    return a * x**2 + b * x + c"""

ANALYTICAL_POLYNOMIAL_TEMPLATE = {
    "category": "Analytical Function",
    "description": "Polynomial function - good for parabolic relationships, response curves",
    "model_name": "PolynomialModel",
    "function_source": SOURCE,
    "function_name": "y",
    "docstring": "Polynomial model template",
    "parameters": [
        {"name": "a", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
        {"name": "b", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
        {"name": "c", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
    ],
    "bounds": [
        {"name": "a", "lower": {"magnitude": -10.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
        {"name": "b", "lower": {"magnitude": -10.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
        {"name": "c", "lower": {"magnitude": -10.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
        {"name": "x", "lower": {"magnitude": -5.0, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
        {"name": "y", "lower": {"magnitude": -10.0, "unit": "dimensionless"}, "upper": {"magnitude": 50.0, "unit": "dimensionless"}},
    ],
    "data_file": "data.csv",
    "input_data": [{"column": "x", "name": "x", "unit": "dimensionless"}],
    "output_data": {"columns": ["y"], "name": "y", "unit": "dimensionless"},
    "optimizer_type": "nlopt",
    "cost_function_type": "mse",
    "max_time": 5,
    "jit_compile": True,
    "optimizer_config": {"use_gradient": True, "tol": 1e-06},
}