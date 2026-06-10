# Reaction System: A + B ⇌ C → D

Fit a mass-action kinetics ODE model to concentration time-series data from a closed reactor. The proposed mechanism is A + B ⇌ C → D: species A and B form an intermediate C reversibly, which then decays irreversibly into product D.

Embed this data inline (non-dimensionalised, only A and D are observed):

```python
t_data = [0.0, 0.1010, 0.2020, 0.3030, 0.4040, 0.5051, 0.6061, 0.7071, 0.8081, 0.9091,
          1.0101, 1.1111, 1.2121, 1.3131, 1.4141, 1.5152, 1.6162, 1.7172, 1.8182, 1.9192]
A_data  = [2.0290, 1.7137, 1.5841, 1.4427, 1.4124, 1.3689, 1.3856, 1.3274, 1.3209, 1.2937,
           1.3266, 1.2772, 1.2905, 1.2254, 1.2295, 1.2353, 1.2729, 1.1759, 1.2225, 1.1762]
D_data  = [0.0063, 0.0246, 0.0413, 0.0580, 0.1175, 0.1896, 0.1932, 0.2150, 0.2419, 0.3471,
           0.3160, 0.3753, 0.3824, 0.4289, 0.4720, 0.4510, 0.4682, 0.5215, 0.5379, 0.5878]
```

Assume isothermal, isochoric, well-mixed conditions. Initial concentrations C₀ = D₀ = 0. Free parameters: A₀ ∈ (1.0, 3.0), B₀ ∈ (0.5, 2.0), k₁ ∈ (0.01, 10), k₋₁ ∈ (0.01, 10), k₂ ∈ (0.01, 10).

Solve with diffrax `Dopri5`, `PIDController(rtol=1e-8, atol=1e-10)`, `max_steps=10_000`. Fit with `mse_cost`. Guard on `result.success` before proceeding.

Run `covariance_estimation(method="inverse_hessian")` on the fitted result.

Derive physical sanity checks:
- `K_eq = k1 / k_minus1` (equilibrium constant of the reversible step)
- `rate_ratio = k2 / k1` (< 1 means the irreversible sink is rate-limiting)
- `stoich_excess = A0 - B0` (conserved stoichiometric surplus)

Export:
- `fitted_A0`, `fitted_B0`, `fitted_k1`, `fitted_k_minus1`, `fitted_k2`
- `std_errors` — dict of param name → std error float
- `r_squared`, `mse_loss`, `n_evals`
- `K_eq`, `rate_ratio`, `stoich_excess`
