import numpy as np

def format_aic_bic_results(
    aic: float,
    bic: float,
    aicc_str: str,
    delta_bic_aic: float,
    scale_label: str,
    scale_est: float,
    log_likelihood_est: float,
    likelihood_method: str,
    cost_function_type: str,
    loss_value: float,
    k_effective: int,
    n_total: int,
    assumes_independence: bool,
    df_effective: int | None,
    n_parameters: int,
    include_scale_param: bool,
    aicc_include_scale: bool,
    n_obs: int | None,
) -> str:

        # Format result
    result_text = f"""# Information Criteria for Model Selection

## AIC and BIC Results
- **AIC (Akaike Information Criterion):** {aic:.2f}
- **BIC (Bayesian Information Criterion):** {bic:.2f}
- **AICc (Corrected AIC for small samples):** {aicc_str}
- **BIC-AIC Penalty Difference:** {delta_bic_aic:.2f}
- **{scale_label}:** {scale_est:.6e}
- **Log-Likelihood Estimate:** {log_likelihood_est:.2f}
- **Likelihood Method:** {likelihood_method}

## Model Properties
- **Loss Function:** {cost_function_type.upper()}
- **Final Loss Value:** {loss_value:.6e}
- **Effective Parameters (k):** {k_effective}
- **Sample Size (n):** {n_total}"""

    # Add independence assumption warning if applicable
    if assumes_independence:
        result_text += f"""

⚠️  **Independence Assumption**: Sample size (n={n_total}) was inferred by counting all scalar values
in output data. This assumes each scalar is an independent residual, which may be incorrect for:
- Multi-output models (correlated outputs)
- Time series data (temporal correlation)
- Spatial data (spatial correlation)
- Hierarchical/grouped data (within-group correlation)

If residuals are not independent, the effective sample size is smaller and AIC/BIC may be unreliable."""

    # Add parameter settings summary
    result_text += """

## Parameter Settings
"""

    # Document the key parameter choices
    if df_effective is not None:
        result_text += f"- **Degrees of Freedom:** Using df_effective = {df_effective} (penalized/constrained model)\n"
    else:
        result_text += f"- **Degrees of Freedom:** Using k_params = {n_parameters} (standard MLE)\n"

    scale_status = "included" if include_scale_param else "excluded"
    result_text += f"- **Scale Parameter:** {scale_status} in AIC/BIC complexity penalty\n"

    aicc_scale_status = "included" if aicc_include_scale else "excluded"
    result_text += f"- **AICc Scale Parameter:** {aicc_scale_status} in small-sample correction\n"

    if n_obs is not None:
        result_text += f"- **Sample Size:** Explicit n_obs = {n_obs} provided\n"
    else:
        result_text += f"- **Sample Size:** Inferred n = {n_total} from output data (independence assumed)\n"

    result_text += """

## Interpretation Guidelines

### For Model Comparison:
- **Lower AIC/BIC values indicate better models**
- **AIC:** Optimizes predictive performance (allows more complexity)
- **BIC:** Prefers simpler models (stronger complexity penalty)

### Rule of Thumb for Model Selection:
- **ΔAICᵢ < 2:** Substantial support for model i
- **2 ≤ ΔAICᵢ ≤ 7:** Less support for model i
- **ΔAICᵢ > 10:** Essentially no support for model i

Where ΔAICᵢ = AICᵢ - AIC_best

### Loss Function Considerations:
"""

    if cost_function_type == "mse":
        result_text += "- **MSE:** Uses exact Gaussian likelihood - AIC/BIC directly applicable"
    elif cost_function_type == "mae":
        result_text += "- **MAE:** Uses exact Laplace likelihood (no Gaussian conversion)"

    result_text += f"""

### Sample Size Assessment:
- **Current n = {n_total}:** """

    if n_total < 40:
        result_text += "Small sample - AICc strongly recommended over AIC"
        preferred_criterion = "AICc"
    elif n_total < 150:
        result_text += "Moderate sample - Both AIC and BIC reliable, AICc still beneficial"
        preferred_criterion = "AIC or BIC"
    else:
        result_text += "Large sample - BIC becomes more reliable for consistent model selection"
        preferred_criterion = "BIC"

    # Add information about the penalty terms (use the returned k_effective)
    aic_penalty = 2 * k_effective
    bic_penalty = k_effective * np.log(max(n_total, 1))

    # Format conditional values to avoid f-string errors
    ratio_str = f"{bic_penalty / aic_penalty:.2f}" if aic_penalty > 0 else "N/A"

    result_text += f"""

### Complexity Penalties:
- **AIC Penalty:** {aic_penalty:.2f} (2k)
- **BIC Penalty:** {bic_penalty:.2f} (k⋅ln(n))
- **BIC/AIC Penalty Ratio:** {ratio_str}

{"**BIC penalizes complexity more heavily than AIC**" if bic_penalty > aic_penalty else "**AIC and BIC penalties are similar**"}

### Recommended Criterion: **{preferred_criterion}**

### Bayesian vs Frequentist Perspective:
- **BIC**: Bayesian approach - consistent model selection (identifies true model as n→∞)
- **AIC**: Frequentist approach - optimal prediction (minimizes expected prediction error)
- **AICc**: Small-sample correction - unbiased AIC estimation for finite samples

### Model Comparison Protocol:
1. **Calculate ΔIC = IC_i - IC_best** for each model
2. **Akaike weights**: w_i = exp(-ΔAIC_i/2) / Σexp(-ΔAIC_j/2)
3. **Evidence ratios**: ER = exp(ΔAIC/2) (how many times more likely is best model)
"""

    return result_text



def format_ic_error(e: Exception) -> str:
    return f"""❌ **AIC/BIC Calculation Failed**

**Error:** {e!s}

## Troubleshooting:
- Ensure loss_value is non-negative from a successful optimization
- Verify cost_function_type is 'mse' (Gaussian) or 'mae' (Laplace) only
- Check that output data matches the data used in optimization
- Confirm n_parameters counts only the fitted parameters (not fixed constants)
- For multidimensional data: [[sample1_dim1, sample1_dim2], [sample2_dim1, sample2_dim2], ...]

## For Other Loss Functions:
- **Huber loss**: Use TIC (Takeuchi Information Criterion) or cross-validation
- **Relative MSE**: Use cross-validation or heteroscedastic Gaussian likelihood

## Parameter Counting Tips:
- Count only parameters that were optimized (have bounds)
- Exclude input variables and constants
- For neural networks: count weights and biases
- For ODEs: count kinetic parameters and initial conditions
"""

