# Exponential Decay with Uncertainty Quantification

Fit an exponential decay model y = A·exp(-k·t) + c to synthetic data, then compute per-parameter standard errors.

Generate the data inline (no file I/O): use `jnp.linspace(0.0, 5.0, 60)` for time points with true parameters A=2.0, k=0.5, c=0.1, and iid Gaussian noise σ=0.02 (numpy random seed 1).

The model:
```
def decay(params, inputs):
    t = inputs["t"]
    return {"y": params["A"] * jnp.exp(-params["k"] * t) + params["c"]}
```

Fit with `mse_cost`. Bounds: A ∈ (0, 10), k ∈ (0.001, 5), c ∈ (-1, 1). Initial guess: A=1.0, k=0.1, c=0.0.

After fitting, guard on `result.success` before proceeding. Then:
1. Run `covariance_estimation` with `method="sandwich"` (robust to mild model misspecification — does not require exact likelihood)
2. Extract eigenvalues from the covariance result to check for flat directions or ill-conditioning

Export:
- `fitted_A`, `fitted_k`, `fitted_c`
- `std_A`, `std_k`, `std_c` (from `cov.std_errors`)
- `mse_loss`
- `hessian_eigenvalues` — list of floats, sorted ascending
- `condition_number` — max eigenvalue / min eigenvalue (export `inf` if min ≤ 0)
- `truth_vs_fit` — dict keyed by param name, each value a dict with `truth`, `fitted`, `abs_error`, `relative_error_percent`
