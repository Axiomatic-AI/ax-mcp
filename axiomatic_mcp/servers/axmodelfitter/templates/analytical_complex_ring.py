SOURCE = """def T(wls, wl0, neff_0, dneff_dwl, loss, ring_length, coupling):
def compute_neff(wls, wl0, neff_0, dneff_dwl):
    return neff_0 + dneff_dwl * (wls - wl0)

def compute_phi(wls, n, ring_length):
    return 2 * jnp.pi * n * ring_length / wls

neff = compute_neff(wls, wl0, neff_0, dneff_dwl)
phi = compute_phi(wls, neff, ring_length)

transmission = 1 - coupling

out = jnp.sqrt(transmission) - 10 ** (-loss * ring_length / 20.0) * jnp.exp(1j * phi)
out /= 1 - jnp.sqrt(transmission) * 10 ** (-loss * ring_length / 20.0) * jnp.exp(1j * phi)
detected = jnp.abs(out) ** 2
return detected
"""

ANALYTICAL_COMPLEX_RING_TEMPLATE = {
    "category": "Complex Analytical Function",
    "description": "This models a ring resonator with a complex transfer function.",
    "model_name": "RingResonatorModel",
    "function_source": SOURCE,
    "function_name": "T",
    "docstring": "RingResonatorModel - power transfer from input to output for a ring resonator",
    "parameters": [
        {"name": "neff_0", "value": {"magnitude": 2.3, "unit": "dimensionless"}},
        {"name": "dneff_dwl", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
        {"name": "loss", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
        {"name": "ring_length", "value": {"magnitude": 30.0, "unit": "dimensionless"}},
        {"name": "coupling", "value": {"magnitude": 0.3, "unit": "dimensionless"}},
    ],
    "bounds": [
        {"name": "T", "lower": {"magnitude": -0.1, "unit": "dimensionless"}, "upper": {"magnitude": 1.1, "unit": "dimensionless"}},
        {"name": "wls", "lower": {"magnitude": 1.0, "unit": "dimensionless"}, "upper": {"magnitude": 2.0, "unit": "dimensionless"}},
        {"name": "wl0", "lower": {"magnitude": 1.0, "unit": "dimensionless"}, "upper": {"magnitude": 2.0, "unit": "dimensionless"}},
        {"name": "neff_0", "lower": {"magnitude": 2.2, "unit": "dimensionless"}, "upper": {"magnitude": 2.4, "unit": "dimensionless"}},
        {"name": "dneff_dwl", "lower": {"magnitude": -0.4, "unit": "dimensionless"}, "upper": {"magnitude": 0.4, "unit": "dimensionless"}},
        {"name": "loss", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 0.5, "unit": "dimensionless"}},
        {"name": "ring_length", "lower": {"magnitude": 27.0, "unit": "dimensionless"}, "upper": {"magnitude": 33.0, "unit": "dimensionless"}},
        {"name": "coupling", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 0.8, "unit": "dimensionless"}},
    ],
    "constants": [{"name": "wl0", "value": {"magnitude": 1.55, "unit": "dimensionless"}}],
    "data_file": "data.csv",
    "input_data": [{"column": "wavelength", "name": "wls", "unit": "dimensionless"}],
    "output_data": {"columns": ["transmission"], "name": "T", "unit": "dimensionless"},
    "optimizer_type": "nlopt",
    "cost_function_type": "mse",
    "max_time": 5,
    "jit_compile": True,
    "optimizer_config": {"use_gradient": True, "tol": 1e-06},
}
