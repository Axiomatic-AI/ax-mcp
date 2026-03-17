SOURCE = """def f(x, y, a, b, c):
    return a*x**2 + b*y**2 + c"""

ANALYTICAL_MULTIVARIATE_TEMPLATE = {
    "category": "Analytical Function",
    "description": "Multivariate polynomial of order 2 - shows how to deal with mulitple inputs",
    "model_name": "MultivariatePolynomialModel",
    "function_source": SOURCE,
    "function_name": "f",
    "docstring": "Multiple input varaibles template",
    "parameters": [
        {"name": "a", "value": {"magnitude": 2.0, "unit": "dimensionless"}},
        {"name": "b", "value": {"magnitude": 0.5, "unit": "dimensionless"}},
        {"name": "c", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
    ],
    "bounds": [
        {"name": "x", "lower": {"magnitude": -1.0, "unit": "dimensionless"}, "upper": {"magnitude": 1.0, "unit": "dimensionless"}},
        {"name": "y", "lower": {"magnitude": -1.0, "unit": "dimensionless"}, "upper": {"magnitude": 1.0, "unit": "dimensionless"}},
        {
            "name": "f",
            "lower": {"magnitude": -float("inf"), "unit": "dimensionless"},
            "upper": {"magnitude": float("inf"), "unit": "dimensionless"},
        },
        {"name": "a", "lower": {"magnitude": -2.0, "unit": "dimensionless"}, "upper": {"magnitude": 2.0, "unit": "dimensionless"}},
        {"name": "b", "lower": {"magnitude": -2.0, "unit": "dimensionless"}, "upper": {"magnitude": 2.0, "unit": "dimensionless"}},
        {"name": "c", "lower": {"magnitude": -2.0, "unit": "dimensionless"}, "upper": {"magnitude": 2.0, "unit": "dimensionless"}},
    ],
    "data_file": "data.csv",
    "input_data": [{"column": "x", "name": "x", "unit": "dimensionless"}, {"column": "y", "name": "y", "unit": "dimensionless"}],
    "output_data": {"columns": ["f"], "name": "f", "unit": "dimensionless"},
    "optimizer_type": "nlopt",
    "cost_function_type": "mse",
    "max_time": 5,
    "jit_compile": True,
    "optimizer_config": {"use_gradient": True, "tol": 1e-06},
}
