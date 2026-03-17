SOURCE = """def y(t, amplitude, frequency, phase, offset):
return amplitude * jnp.sin(2 * jnp.pi * frequency * t + phase) + offset"""

ANALYTICAL_TRIGONOMETRIC_TEMPLATE = {
    "category": "Analytical Function",
    "description": "Sinusoidal oscillation - good for periodic signals, vibrations, waves",
    "model_name": "SinusoidalModel",
    "function_source": SOURCE,
    "function_name": "y",
    "docstring": "Sinusoidal model template",
    "parameters": [
        {"name": "amplitude", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
        {"name": "frequency", "value": {"magnitude": 0.5, "unit": "dimensionless"}},
        {"name": "phase", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
        {"name": "offset", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
    ],
    "bounds": [
        {"name": "amplitude", "lower": {"magnitude": 0.1, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
        {"name": "frequency", "lower": {"magnitude": 0.1, "unit": "dimensionless"}, "upper": {"magnitude": 2.0, "unit": "dimensionless"}},
        {"name": "phase", "lower": {"magnitude": -3.14, "unit": "dimensionless"}, "upper": {"magnitude": 3.14, "unit": "dimensionless"}},
        {"name": "offset", "lower": {"magnitude": -2.0, "unit": "dimensionless"}, "upper": {"magnitude": 2.0, "unit": "dimensionless"}},
        {"name": "t", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
        {"name": "y", "lower": {"magnitude": -3.0, "unit": "dimensionless"}, "upper": {"magnitude": 3.0, "unit": "dimensionless"}},
    ],
    "data_file": "data.csv",
    "input_data": [{"column": "time", "name": "t", "unit": "dimensionless"}],
    "output_data": {"columns": ["amplitude"], "name": "y", "unit": "dimensionless"},
    "optimizer_type": "nlopt",
    "cost_function_type": "mse",
    "max_time": 5,
    "jit_compile": True,
    "optimizer_config": {"use_gradient": True, "tol": 1e-06},
}
