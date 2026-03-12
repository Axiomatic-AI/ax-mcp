SOURCE = """import diffrax
import jax.numpy as jnp

def c_obs(ts, A0, B0, C0, D0, k1, k2, k3):
    def dc(t, c, p):
        k1, k2, k3 = p
        A, B, C, D = c
        dA = -k1 * A * B + k2 * C
        dB = -k1 * A * B + k2 * C
        dC = k1 * A * B - k2 * C - k3 * C
        dD = k3 * C
        return jnp.array([dA, dB, dC, dD])

    c0 = jnp.array([A0, B0, C0, D0])
    k = jnp.array([k1, k2, k3])

    saveat = diffrax.SaveAt(ts=ts)
    sol = diffrax.diffeqsolve(
        diffrax.ODETerm(dc),
        diffrax.Dopri5(),
        t0=0.0,
        t1=ts[-1],
        dt0=0.01,
        y0=c0,
        args=k,
        saveat=saveat,
    )
    return sol.ys[:, [0, 3]]"""

ODE_SYSTEM_TEMPLATE = {
    "category": "ODE System",
    "description": "Chemical reactor model for the reaction A+B <=> C => D is happening. Concentrations of A and D are observed.",
    "model_name": "ODESystem",
    "function_source": SOURCE,
    "function_name": "c_obs",
    "docstring": "ODE model template",
    "parameters": [
        {"name": "A0", "value": {"magnitude": 2.0, "unit": "dimensionless"}},
        {"name": "B0", "value": {"magnitude": 2.0, "unit": "dimensionless"}},
        {"name": "C0", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
        {"name": "D0", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
        {"name": "k1", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
        {"name": "k2", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
        {"name": "k3", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
    ],
    "bounds": [
        {
            "name": "A0",
            "lower": {"magnitude": 0.0, "unit": "dimensionless"},
            "upper": {"magnitude": 5.0, "unit": "dimensionless"},
        },
        {
            "name": "B0",
            "lower": {"magnitude": 0.0, "unit": "dimensionless"},
            "upper": {"magnitude": 5.0, "unit": "dimensionless"},
        },
        {
            "name": "C0",
            "lower": {"magnitude": 0.0, "unit": "dimensionless"},
            "upper": {"magnitude": 5.0, "unit": "dimensionless"},
        },
        {
            "name": "D0",
            "lower": {"magnitude": 0.0, "unit": "dimensionless"},
            "upper": {"magnitude": 5.0, "unit": "dimensionless"},
        },
        {
            "name": "k1",
            "lower": {"magnitude": 0.0, "unit": "dimensionless"},
            "upper": {"magnitude": 5.0, "unit": "dimensionless"},
        },
        {
            "name": "k2",
            "lower": {"magnitude": 0.0, "unit": "dimensionless"},
            "upper": {"magnitude": 5.0, "unit": "dimensionless"},
        },
        {
            "name": "k3",
            "lower": {"magnitude": 0.0, "unit": "dimensionless"},
            "upper": {"magnitude": 5.0, "unit": "dimensionless"},
        },
        {
            "name": "ts",
            "lower": {"magnitude": 0.0, "unit": "dimensionless"},
            "upper": {"magnitude": 5.0, "unit": "dimensionless"},
        },
        {
            "name": "c_obs",
            "lower": {"magnitude": 0.0, "unit": "dimensionless"},
            "upper": {"magnitude": 10.0, "unit": "dimensionless"},
        },
    ],
    "constants": [],
    "data_file": "data.csv",
    "input_data": [{"column": "time", "name": "ts", "unit": "dimensionless"}],
    "output_data": {"columns": ["concentration_A", "concentration_D"], "name": "c_obs", "unit": "dimensionless"},
    "optimizer_type": "nlopt",
    "cost_function_type": "mse",
    "max_time": 5,
    "jit_compile": True,
    "optimizer_config": {"use_gradient": True, "tol": 1e-06},
}