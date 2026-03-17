SOURCE = """def y(t, amplitude, decay_rate, offset):
    return amplitude * jnp.exp(-decay_rate * t) + offset"""

ANALYTICAL_EXPONENTIAL_TEMPLATE = {
    "category": "Analytical Function",
    "description": "Single exponential decay/growth with offset - good for radioactive decay, signal attenuation, population growth",
    "model_name": "ExponentialModel",
    "function_source": SOURCE,
    "function_name": "y",
    "docstring": "Exponential model template",
    "parameters": [
        {"name": "amplitude", "value": {"magnitude": 2.0, "unit": "dimensionless"}},
        {"name": "decay_rate", "value": {"magnitude": 0.5, "unit": "dimensionless"}},
        {"name": "offset", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
    ],
    "bounds": [
        {"name": "amplitude", "lower": {"magnitude": 0.1, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
        {"name": "decay_rate", "lower": {"magnitude": 0.01, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
        {"name": "offset", "lower": {"magnitude": -5.0, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
        {"name": "t", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
        {"name": "y", "lower": {"magnitude": -1.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
    ],
    "data_file": "data.csv",
    "input_data": [{"column": "time", "name": "t", "unit": "dimensionless"}],
    "output_data": {"columns": ["signal"], "name": "y", "unit": "dimensionless"},
    "optimizer_type": "nlopt",
    "cost_function_type": "mse",
    "max_time": 5,
    "jit_compile": True,
    "optimizer_config": {"use_gradient": True, "tol": 1e-06},
}
