import numpy as np

from axiomatic_mcp.shared.api_client import AxiomaticAPIClient

def compute_aic_bic_from_loss_and_data(
    loss_value,
    cost_function_type,
    output_magnitudes,
    n_parameters,
    sigma,
    include_scale_param=True,
    n_obs=None,
    df_effective=None,
    aicc_include_scale=True,
    n_scale_params=1,
):
    """Compute AIC/BIC criteria from loss value and target data with comprehensive statistics.

    This is a wrapper around aic_bic_from_loss() that integrates with the server's data structures
    and provides additional computed statistics for display.

    Args:
        loss_value: Mean loss per observation (MSE for Gaussian, MAE for Laplace)
        cost_function_type: 'mse' or 'mae' (maps to loss_type in aic_bic_from_loss)
        output_magnitudes: Target data values (used to determine sample size if n_obs not provided)
        n_parameters: Number of parameters in the mean function (excluding scale)
        include_scale_param: If True, add 1 to effective parameter count for scale parameter
        n_obs: Explicit count of independent residuals. If None, infers from output_magnitudes.size
               WARNING: Inference assumes every scalar is an independent residual, which may be
               incorrect for multi-output, time series, or spatially correlated data.
        df_effective: Effective degrees of freedom for penalized/constrained models (EXCLUDING
               scale parameter). If provided, used instead of n_parameters.
        aicc_include_scale: If True, include scale parameter in AICc correction. Literature varies
               on this convention - some include scale, others exclude it from small-sample correction.
        n_scale_params: Number of scale parameters to penalize when include_scale_param=True.
               For single-output models: use 1 (default). For multi-output models with separate
               noise scales per output dimension: use number_of_outputs.
        sigma: REQUIRED noise standard deviation for diagonal covariance Σ = σ²I.
               For 'mse': must be provided from domain knowledge. For 'mae': pass None.

    Returns:
        dict: Comprehensive statistics including AIC, BIC, AICc, scale estimates, etc.
        Also includes 'assumes_independence' flag when n_obs was inferred.
    """  # noqa
    if n_obs is None:
        y_true = np.asarray(output_magnitudes)
        n_obs = int(y_true.size)
        assumes_independence = True
    else:
        assumes_independence = False

    if n_obs == 0:
        return {
            "aic": np.nan,
            "bic": np.nan,
            "aicc": np.nan,
            "n_total": 0,
            "log_likelihood_est": np.nan,
            "delta_bic_aic": np.nan,
            "scale_est": np.nan,
            "k_effective": 0,
            "sigma_squared_est": np.nan,
            "assumes_independence": assumes_independence,
        }

    # Call the core statistical function
    res = aic_bic_from_loss(
        loss_value,
        cost_function_type,
        n_obs,
        n_parameters,
        sigma,
        include_scale_param=include_scale_param,
        use_aicc=True,
        df_effective=df_effective,
        aicc_include_scale=aicc_include_scale,
        n_scale_params=n_scale_params,
    )

    # Family-specific scale estimate for display (loss_value is always mean per observation)
    scale_est = loss_value  # σ² for MSE, b for MAE

    # Legacy field: only populate sigma_squared_est for Gaussian; otherwise np.nan
    sigma_squared_est = scale_est if cost_function_type == "mse" else np.nan

    return {
        "aic": res["aic"],
        "bic": res["bic"],
        "aicc": res["aicc"],
        "n_total": res["n"],
        "log_likelihood_est": -0.5 * res["neg2loglik"],
        "delta_bic_aic": res["bic"] - res["aic"],
        "scale_est": scale_est,
        "k_effective": res["k"],
        "sigma_squared_est": sigma_squared_est,  # Legacy field: only for Gaussian
        "assumes_independence": assumes_independence,
    }

def evaluate_loss(payload: dict) -> dict:
    """Evaluate the loss/cost of a model using the provided payload.

    Args:
        payload: Complete request payload for the cost evaluation API

    Returns:
        Dict with cost_value and any other response fields

    Raises:
        Exception: If API call fails
    """
    with AxiomaticAPIClient() as client:
        response = client.post("/digital-twin/custom_evaluate_cost", data=payload)

    return response

def aic_bic_from_loss(
    loss_value,
    loss_type,
    n_obs,
    k_params,
    sigma,
    *,
    include_scale_param=True,
    use_aicc=True,
    aicc_include_scale=True,
    df_effective=None,
    n_scale_params=1,
):
    """Compute AIC and BIC from loss value using the likelihood for each loss family.

    Supported loss families:
    - MSE (Gaussian): Uses general Gaussian likelihood with diagonal covariance Σ = σ²I
    - MAE (Laplace): Uses exact Laplace likelihood with scale b = MAE

    Mathematical Foundation:
    - Gaussian: -2 log L = n*log(2π) + n*log(σ²) + RSS/σ²
      where RSS = MSE * n, so -2 log L = n*log(2π) + n*log(σ²) + n*MSE/σ²
    - Laplace: -2 log L = 2n[log(2b) + 1] where b = MAE
    - AIC = -2 log L + 2k_eff
    - BIC = -2 log L + k_eff log(n)
    - AICc = AIC + 2k_aicc(k_aicc + 1)/(n - k_aicc - 1) [Gaussian only]

    DIAGONAL COVARIANCE: Assumes Σ = σ²I (diagonal covariance with constant variance
    σ² across all observations). Requires user to provide σ from domain knowledge.

    PARAMETER COUNTING: Since σ is user-provided (not estimated), include_scale_param
    should typically be False since σ is fixed, not fitted.

    Args:
        loss_value: Mean loss per observation (MSE for Gaussian, MAE for Laplace)
        loss_type: 'mse' or 'mae' (Huber/relative_mse not supported - use TIC/WAIC/CV)
        n_obs: count of (conditionally) independent scalar residuals
        k_params: parameters in the mean function (exclude scale); effective k may add +1
        sigma: Noise standard deviation for diagonal covariance Σ = σ²I. REQUIRED for 'mse'.
               Not used for 'mae' (pass None).
        include_scale_param: If True, add 1 for scale parameter count. Should be False
                           when sigma is user-provided (not fitted).
        use_aicc: Apply AICc correction (Gaussian only, requires n > k + 1)
        aicc_include_scale: If True, include scale parameter in k for AICc.
        df_effective: Effective degrees of freedom for penalized/constrained models
            (EXCLUDING scale parameter). If provided, used instead of k_params.
        n_scale_params: Number of scale parameters to penalize when include_scale_param=True.

    Returns:
        dict: Contains 'aic', 'bic', 'aicc', 'neg2loglik', 'k', 'n', 'loss_type', 'sigma_used'
    """  # noqa
    if n_obs <= 0 or loss_value < 0:
        return {"aic": np.nan, "bic": np.nan, "aicc": np.nan, "neg2loglik": np.nan, "k": 0, "n": n_obs, "loss_type": loss_type}

    # Use effective degrees of freedom if provided, otherwise use parameter count
    if df_effective is not None:
        k_eff = float(df_effective + (n_scale_params if include_scale_param else 0))
    else:
        k_eff = int(k_params + (n_scale_params if include_scale_param else 0))

    if loss_type == "mse":
        if sigma is None:
            raise ValueError(
                "sigma parameter is required for 'mse' (Gaussian) likelihood calculation. "
                "Provide the noise standard deviation for diagonal covariance Σ = σ²I."  # noqa: RUF001
            )

        # General Gaussian likelihood: -2 log L = n*log(2π) + n*log(σ²) + RSS/σ²
        # RSS = MSE * n, so RSS/σ² = n*MSE/σ²
        sigma2_user = max(sigma**2, 1e-300)
        neg2loglik = n_obs * (np.log(2 * np.pi) + np.log(sigma2_user)) + n_obs * loss_value / sigma2_user
        sigma_used = sigma
    elif loss_type == "mae":
        if sigma is not None:
            raise ValueError("sigma parameter is only supported for 'mse' (Gaussian) loss type, not 'mae' (Laplace)")
        b = max(loss_value, 1e-300)  # MAE = (1/n) Σ|r|
        neg2loglik = 2 * n_obs * (np.log(2 * b) + 1)
        sigma_used = None

    else:
        raise NotImplementedError(
            f"Loss type '{loss_type}' not supported. Use 'mse' (Gaussian) or 'mae' (Laplace). "
            "For Huber or relative_mse, use TIC/WAIC/cross-validation instead."
        )

    # AIC and BIC always use k_eff (includes scale if include_scale_param=True)
    aic = neg2loglik + 2 * k_eff
    bic = neg2loglik + k_eff * np.log(max(n_obs, 1))
    aicc = np.inf

    # AICc only for Gaussian case with sufficient sample size
    # NOTE: AICc can use different k than AIC/BIC based on aicc_include_scale parameter
    if use_aicc and loss_type == "mse":
        # Build k_aicc from the same base used for k_eff (respects df_effective)
        base_k = float(df_effective) if df_effective is not None else float(k_params)
        k_aicc = base_k + (float(n_scale_params) if (include_scale_param and aicc_include_scale) else 0.0)
        if n_obs > k_aicc + 1:
            aicc = aic + (2 * k_aicc * (k_aicc + 1)) / (n_obs - k_aicc - 1)

    return {
        "aic": float(aic),
        "bic": float(bic),
        "aicc": float(aicc),
        "neg2loglik": float(neg2loglik),
        "k": k_eff,
        "n": n_obs,
        "loss_type": loss_type,
        "sigma_used": sigma_used,
    }