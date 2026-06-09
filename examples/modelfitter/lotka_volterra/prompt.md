# Lotka-Volterra Predator-Prey ODE Fit

Fit a Lotka-Volterra predator-prey ODE to non-dimensionalised time series data and estimate per-parameter uncertainty.

The system:
```
dx/dt = a·x - b·x·y    (prey)
dy/dt = c·x·y - d·y    (predator)
```
Six free parameters: rates (a, b, c, d) and initial conditions (x0, y0).

Embed this data inline:

```python
t_data    = [0.0, 1.0101, 2.0202, 3.0303, 4.0404, 5.0505, 6.0606, 7.0707, 8.0808, 9.0909, 10.1010, 11.1111, 12.1212, 13.1313, 14.1414, 15.1515, 16.1616, 17.1717, 18.1818, 19.1919]
prey_data = [0.6452, 0.3070, 0.4472, 0.3277, 0.7491, 1.2495, 2.2643, 2.3120, 0.9438, 0.3529, 0.5235, 0.4183, 0.7489, 0.8741, 1.6189, 2.4449, 1.8870, 0.3456, 0.4107, 0.2398]
pred_data = [1.2316, 0.6899, 0.3110, 0.0747, 0.1265, 0.2934, 0.2204, 0.7193, 1.3216, 1.1461, 0.3762, 0.2984, 0.0939, 0.1578, 0.2735, 0.2921, 1.1531, 1.2293, 0.6318, 0.4541]
```

Solve with diffrax `Dopri5`, `PIDController(rtol=1e-8, atol=1e-10)`, `max_steps=10_000`.

**Important:** use `diffrax.DirectAdjoint()` as the `adjoint` argument — this stores the full forward trajectory and enables exact reverse-over-reverse AD for the Hessian needed by `covariance_estimation`. Do NOT use `RecursiveCheckpointAdjoint` here.

Bounds: a ∈ (0.5, 1.2), b ∈ (0.8, 1.5), c ∈ (0.5, 1.0), d ∈ (0.5, 1.0). Initial conditions bounded at ±50% around the first data points.

After fitting (guard on `result.success`), run `covariance_estimation` with `method="inverse_hessian"`. Then compute equilibrium populations: x_eq = d/c, y_eq = a/b.

Export:
- `fitted_a`, `fitted_b`, `fitted_c`, `fitted_d`, `fitted_x0`, `fitted_y0`
- `std_errors` — dict of param name → std error float
- `hessian_eigenvalues` — list sorted ascending
- `condition_number`
- `equilibrium_prey` (d/c), `equilibrium_predator` (a/b)
- `mse_loss`, `n_evals`, `r_squared`
