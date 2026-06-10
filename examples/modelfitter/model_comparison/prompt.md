# Polynomial Model Selection with AIC/BIC

Fit three polynomial candidates (linear, quadratic, cubic) to the same noisy dataset and rank them by information criteria to identify the best-complexity model.

Generate data inline: 60 points over x ∈ [−2, 2] with the true underlying relationship being quadratic (a=0.5, b=−0.8, c=0.4) plus iid Gaussian noise σ=0.05 (JAX random key 30). The quadratic model should emerge as the winner — it captures all the signal without overfitting.

Fit all three candidates with `mse_cost`. Guard on `result.success` for each fit before comparing. Compare the fitted models using `compare_models` with `isotropic_gaussian_likelihood()`.

Export:
- For each model (`linear`, `quadratic`, `cubic`): `aic`, `bic`, `aicc`, `delta_aic`, `akaike_weight`, `n_params`
- `preferred_model` — name of the model with lowest AIC
- `preferred_akaike_weight`
- `truth_vs_fit_quadratic` — dict keyed by param name, each value a dict with `truth`, `fitted`, `abs_error`, `relative_error_percent`
- `cubic_spurious_d` — the cubic model's extra coefficient (should be near zero for well-specified data)
