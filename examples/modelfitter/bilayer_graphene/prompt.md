# Bilayer Graphene Dual-Gate Transport Fit

Fit a physics-informed 10-parameter model for sheet resistance R(V_TG, V_BG) of bilayer graphene under dual electrostatic gating.

The model combines a Drude conductivity term (mobility-modulated carrier transport) with a residual conductivity floor (quantum/thermal transport suppressed by gap opening):

$$R = \frac{1}{\sigma_\text{drude} + \sigma_\text{min}} \times 10^{-3} + R_c \quad [\text{k}\Omega]$$

The displacement fields D_T = V_TG − V_TG0 and D_B = V_BG − V_BG0 control: (1) carrier density n ∝ |D_B − D_T| via field-effect gating through a dielectric (ε_r = 3.9, d = 0.35 nm), (2) bandgap Δ = β|D̄| where D̄ is the average field, (3) mobility μ(D̄) = μ₀ / (1 + α|D̄|^p), (4) residual conductivity σ_min = σ₀₀ / (1 + |Δ/Δ₀|^q). Drude conductivity is σ_drude = g_s g_v e n μ with spin/valley degeneracy g_s = g_v = 2.

Generate synthetic data inline: V_TG = `jnp.linspace(-2.0, 2.0, 50)`, V_BG ∈ {−1.5, −1.0, −0.5, 0.5, 1.0, 1.5} V (meshgrid, flattened → 300 points). True parameters: mu0=0.6, alpha=2.0, p=2.0, sigma00=1e-4, Delta0=1.5, q=2.0, beta=0.02, VTG0=0.05, VBG0=−0.05, Rc=0.15. Add iid Gaussian noise σ=0.005 kΩ (numpy random seed 42).

Bounds: mu0 ∈ (0.1, 2.0), alpha ∈ (0.5, 5.0), p ∈ (1.0, 3.0), sigma00 ∈ (1e-5, 5e-4), Delta0 ∈ (0.02, 2.0), q ∈ (1.0, 4.0), beta ∈ (0.005, 0.05), VTG0 ∈ (−0.3, 0.3), VBG0 ∈ (−0.3, 0.3), Rc ∈ (0.05, 0.5). Fit with `mse_cost`. Guard on `result.success`.

Run `covariance_estimation(method="inverse_hessian")`.

Export:
- All 10 fitted parameter values
- `std_errors` — dict of param name → std error float
- `r_squared`, `mse_loss`, `n_evals`
- `truth_vs_fit` — dict keyed by param name, each value a dict with `truth`, `fitted`, `abs_error`, `relative_error_percent`
