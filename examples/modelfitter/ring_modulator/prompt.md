# Ring Modulator Transmission Fit

Fit a 5-parameter transfer-matrix model for a ring modulator to transmission data measured across wavelength and bias voltage.

The model is:

$$T(\lambda, V) = \left|\frac{t - a\,e^{2\pi j\,n(V)L/\lambda}}{1 - t\,a\,e^{2\pi j\,n(V)L/\lambda}}\right|^2$$

with $t = \sqrt{1-\kappa}$, $a = 10^{-\alpha L/20}$, and an effective refractive index $n(V) = n_0 + g_n V$ that shifts linearly with bias.

Generate synthetic data inline: wavelengths `jnp.linspace(1.5, 1.6, 100)` μm at 5 bias voltages `[0.0, 0.5, 1.0, 1.5, 2.0]` V (meshgrid, flattened). True parameters: n0=2.35, gn=0.018, L=5.0, alpha=0.3, kappa=0.25. Add iid Gaussian noise σ=0.01 (numpy random seed 7).

Bounds: n0 ∈ (2.2, 2.4), gn ∈ (−0.05, 0.05), L ∈ (4.5, 5.5) μm, alpha ∈ (0.0, 0.6), kappa ∈ (0.1, 0.5). Fit with `mse_cost`. Guard on `result.success`.

Run `covariance_estimation(method="sandwich")` on the fitted result.

Export:
- `fitted_n0`, `fitted_gn`, `fitted_L`, `fitted_alpha`, `fitted_kappa`
- `std_errors` — dict of param name → std error float
- `r_squared`, `mse_loss`
- `truth_vs_fit` — dict keyed by param name, each value a dict with `truth`, `fitted`, `abs_error`, `relative_error_percent`
