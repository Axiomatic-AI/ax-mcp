# Ring Resonator Lineshape Fit with Model Comparison

Fit the transmission dip of a ring resonator vs frequency detuning, compare Lorentzian vs Gaussian lineshapes via AIC, and quantify uncertainty on the winning model.

Embed this data inline (detuning in GHz, transmission dimensionless):

```python
detuning_GHz = [-0.2122, -0.2022, -0.1922, -0.1823, -0.1723, -0.1623, -0.1523, -0.1423,
                -0.1323, -0.1223, -0.1123, -0.1023, -0.0923, -0.0823, -0.0723, -0.0623,
                -0.0523, -0.0423, -0.0323, -0.0223, -0.0124, -0.0024,  0.0076,  0.0176,
                 0.0276,  0.0376,  0.0476,  0.0576,  0.0676,  0.0776,  0.0876,  0.0976,
                 0.1076,  0.1176,  0.1276,  0.1376,  0.1476,  0.1575,  0.1675,  0.1775,
                 0.1875,  0.1975,  0.2075,  0.2175,  0.2275,  0.2375,  0.2475,  0.2575,
                 0.2675,  0.2775]
transmission = [1.0025, 0.9959, 1.0035, 1.0119, 0.9939, 0.9934, 1.0110, 1.0021, 0.9889,
                0.9979, 0.9865, 0.9848, 0.9896, 0.9650, 0.9628, 0.9686, 0.9556, 0.9562,
                0.9246, 0.8903, 0.8800, 0.8297, 0.8341, 0.8534, 0.9000, 0.9346, 0.9407,
                0.9683, 0.9668, 0.9757, 0.9768, 1.0044, 0.9880, 0.9794, 0.9996, 0.9803,
                0.9955, 0.9746, 0.9815, 0.9973, 1.0032, 0.9979, 0.9954, 0.9938, 0.9823,
                0.9901, 0.9929, 1.0082, 1.0013, 0.9803]
```

Models (T_max fixed to mean transmission at |Δf| > 0.2 GHz, only T_min and f_h are free):
- **Lorentzian**: T(Δf) = T_max − (T_max − T_min) / (1 + (Δf/f_h)²)
- **Gaussian**: T(Δf) = T_max − (T_max − T_min) · exp(−0.5·(Δf/f_h)²)

Fit both with `mse_cost`. Bounds: T_min ∈ (0.7, 0.95), f_h ∈ (0.005, 0.15) GHz.

Guard on `result.success` for both fits. Compare with `compare_models` using `isotropic_gaussian_likelihood()`.

Then run `covariance_estimation(method="sandwich")` on the Lorentzian fit.

Derive figures of merit:
- `extinction_dB = -10 · log10(T_min / T_max)`
- `Q_factor ≈ 193000 / (2 · f_h)` (assuming carrier at 193 THz ≈ 1550 nm)

Export:
- `fitted_T_min`, `fitted_f_h_GHz`, `r_squared`
- `extinction_dB`, `Q_factor`
- `model_comparison` — list of dicts, one per model, each with: `name`, `aic`, `delta_aic`, `akaike_weight`, `n_params`
- `std_errors` — dict of param name → std error float
