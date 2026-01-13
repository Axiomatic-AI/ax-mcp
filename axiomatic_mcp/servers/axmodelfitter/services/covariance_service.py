"""Service for computing parameter covariance matrices."""

import json

import httpx
import numpy as np

from ....shared import AxiomaticAPIClient
from ....shared.models.singleton_base import SingletonBase


class CovarianceService(SingletonBase):
    """
    Service for computing parameter covariance matrices using the Axiomatic API.

    Provides uncertainty estimates using robust Huber-White sandwich estimator and
    classical inverse Hessian approach.
    """

    async def compute_covariance(self, request_data: dict) -> dict:
        """
        Compute parameter covariance matrices.

        Args:
            request_data: Complete request payload for API containing:
                - model_name: str
                - parameters: list of parameter dicts
                - bounds: list of bound dicts
                - constants: list of constant dicts
                - input: resolved input data dict
                - target: resolved output data dict
                - function_source: str (JAX code)
                - function_name: str
                - docstring: str
                - jit_compile: bool
                - cost_function_type: str
                - scale_params: bool
                - variance: float | None

        Returns:
            dict with keys:
                - success: bool
                - error: str (if failure)
                - parameters: list (input parameters)
                - sandwich_covariance: list[list] | None
                - inverse_hessian_covariance: list[list] | None
                - sandwich_correlation: list[list] | None
                - inverse_hessian_correlation: list[list] | None
                - parameter_names: list[str]
                - sandwich_std_errors: list[float] | None
                - inverse_hessian_std_errors: list[float] | None
                - markdown_report: str (formatted results)
        """
        try:
            # Make API call
            response = self._make_api_call(request_data)

            # Validate response has covariance matrices
            if not self._has_valid_covariance(response):
                return self._format_error_response(response)

            # Process covariance matrices
            processed = self._process_covariance_results(response, request_data["parameters"])

            # Format markdown report
            markdown = self._format_markdown_report(processed, request_data["model_name"], request_data["parameters"])

            return {
                "success": True,
                "markdown_report": markdown,
                "parameters": request_data["parameters"],
                **processed,
            }

        except Exception as e:
            return self._handle_exception(e)

    def _make_api_call(self, request_data: dict) -> dict:
        """
        Make HTTP POST to /digital-twin/compute-parameter-covariance.

        Args:
            request_data: Complete request payload

        Returns:
            API response dict
        """
        with AxiomaticAPIClient() as client:
            return client.post("/digital-twin/compute-parameter-covariance", data=request_data)

    def _has_valid_covariance(self, response: dict) -> bool:
        """
        Check if response contains at least one valid covariance matrix.

        Args:
            response: API response dict

        Returns:
            True if at least one covariance matrix is present and valid
        """
        robust_cov = response.get("sandwich_covariance")
        classical_cov = response.get("inverse_hessian_covariance")
        return (isinstance(robust_cov, list) and len(robust_cov) > 0) or (isinstance(classical_cov, list) and len(classical_cov) > 0)

    def _process_covariance_results(self, response: dict, parameters: list) -> dict:
        """
        Process covariance matrices, compute correlations and standard errors.

        Args:
            response: API response dict
            parameters: List of parameter dicts with names, values, units

        Returns:
            dict with processed matrices:
                - sandwich_covariance: list[list] | None
                - inverse_hessian_covariance: list[list] | None
                - sandwich_correlation: list[list] | None
                - inverse_hessian_correlation: list[list] | None
                - parameter_names: list[str]
                - sandwich_std_errors: list[float] | None
                - inverse_hessian_std_errors: list[float] | None
        """
        # Extract parameter names from response or fall back to input parameters
        param_names = [p["name"] for p in parameters]
        parameter_names = response.get("param_names", param_names)

        # Initialize results
        result = {
            "sandwich_covariance": None,
            "inverse_hessian_covariance": None,
            "sandwich_correlation": None,
            "inverse_hessian_correlation": None,
            "parameter_names": parameter_names,
            "sandwich_std_errors": None,
            "inverse_hessian_std_errors": None,
        }

        # Process robust (sandwich) covariance if available
        robust_cov = response.get("sandwich_covariance")
        if isinstance(robust_cov, list) and len(robust_cov) > 0:
            robust_processed = self._process_single_covariance(robust_cov, parameter_names)
            result["sandwich_covariance"] = robust_cov
            result["sandwich_correlation"] = robust_processed["correlation"]
            result["sandwich_std_errors"] = robust_processed["std_errors"]

        # Process classical (inverse Hessian) covariance if available
        classical_cov = response.get("inverse_hessian_covariance")
        if isinstance(classical_cov, list) and len(classical_cov) > 0:
            classical_processed = self._process_single_covariance(classical_cov, parameter_names)
            result["inverse_hessian_covariance"] = classical_cov
            result["inverse_hessian_correlation"] = classical_processed["correlation"]
            result["inverse_hessian_std_errors"] = classical_processed["std_errors"]

        return result

    def _process_single_covariance(self, cov_matrix: list, parameter_names: list) -> dict:
        """
        Process a single covariance matrix to compute correlation and std errors.

        Args:
            cov_matrix: Covariance matrix as list of lists
            parameter_names: List of parameter names

        Returns:
            dict with:
                - correlation: list[list] (JSON-compatible, NaN -> None)
                - std_errors: list[float]
        """
        cov_array = np.array(cov_matrix)
        std_errors = np.sqrt(np.diag(cov_array))

        # Compute correlation matrix
        normalization_mask = std_errors > 1e-10
        corr_array = np.where(normalization_mask[:, None] & normalization_mask[None, :], cov_array / np.outer(std_errors, std_errors), np.nan)

        # Convert to JSON-compatible format (NaN -> None)
        correlation = [[None if np.isnan(x) else float(x) for x in row] for row in corr_array]

        return {"correlation": correlation, "std_errors": std_errors.tolist()}

    def _format_markdown_report(self, processed: dict, model_name: str, parameters: list) -> str:
        """
        Generate markdown report with covariance analysis results.

        Args:
            processed: Processed covariance results dict
            model_name: Name of the model
            parameters: List of parameter dicts

        Returns:
            Formatted markdown string
        """
        # Create lookup from parameter name to value/unit for robust matching
        param_lookup = {p["name"]: p["value"] for p in parameters}

        result_text = f"""# Parameter Covariance Analysis: {model_name}

Status: Success

## Fitted Parameters
"""

        for param in parameters:
            name = param["name"]
            value = param["value"]["magnitude"]
            unit = param["value"]["unit"]
            result_text += f"- **{name}:** {value:.6g} {unit}\n"

        # Process robust covariance section
        if processed["sandwich_covariance"] is not None:
            result_text += self._format_covariance_section(
                "Robust Covariance (Huber-White Sandwich)",
                processed["sandwich_covariance"],
                processed["sandwich_correlation"],
                processed["sandwich_std_errors"],
                processed["parameter_names"],
                param_lookup,
            )

        # Process classical covariance section
        if processed["inverse_hessian_covariance"] is not None:
            result_text += self._format_covariance_section(
                "Classical Covariance (Inverse Hessian)",
                processed["inverse_hessian_covariance"],
                processed["inverse_hessian_correlation"],
                processed["inverse_hessian_std_errors"],
                processed["parameter_names"],
                param_lookup,
            )

        result_text += "\n## Notes\n"
        result_text += "- Standard errors indicate parameter constraint quality\n"
        result_text += "- Under Gaussianity assumption -- 95% confidence interval: parameter ± 1.96 × std_error\n"
        result_text += "- Correlation near ±1 shows parameters trade off\n"
        result_text += "- Use robust estimators when model may be misspecified\n"

        return result_text

    def _format_covariance_section(
        self,
        section_title: str,
        cov_matrix: list,
        corr_matrix: list,
        std_errors: list,
        parameter_names: list,
        param_lookup: dict,
    ) -> str:
        """
        Format a single covariance section (robust or classical).

        Args:
            section_title: Title for the section
            cov_matrix: Covariance matrix
            corr_matrix: Correlation matrix (JSON-compatible with None for NaN)
            std_errors: List of standard errors
            parameter_names: List of parameter names
            param_lookup: Dict mapping parameter name to value dict

        Returns:
            Formatted markdown section
        """
        result_text = f"\n## {section_title}\n\n"

        # Use covariance matrix dimensions to avoid out-of-bounds access
        cov_array = np.array(cov_matrix)
        n_cov_params = cov_array.shape[0]
        cov_param_names = parameter_names[:n_cov_params]

        # Format standard errors
        result_text += "### Standard Errors\n"
        for name, std_err in zip(cov_param_names, std_errors, strict=False):
            param_info = param_lookup.get(name, {"magnitude": float("nan"), "unit": "?"})
            param_value = param_info["magnitude"]
            param_unit = param_info["unit"]
            relative_error = (std_err / abs(param_value) * 100) if param_value != 0 else float("inf")
            result_text += f"- **{name}:** {std_err:.6g} {param_unit} ({relative_error:.2f}% relative)\n"

        # Format correlation matrix
        result_text += "\n### Correlation Matrix\n"
        result_text += "| Parameter | " + " | ".join(cov_param_names) + " |\n"
        result_text += "|-----------|" + "|".join(["-------"] * len(cov_param_names)) + "|\n"

        for i, name_i in enumerate(cov_param_names):
            row_text = f"| **{name_i}** |"
            for j in range(len(cov_param_names)):
                corr_val = corr_matrix[i][j]
                if corr_val is not None:
                    row_text += f" {corr_val:+.3f} |"
                else:
                    row_text += " N/A |"
            result_text += row_text + "\n"

        return result_text

    def _format_error_response(self, response: dict) -> dict:
        """
        Format error response when API returns no valid covariance.

        Args:
            response: API response dict

        Returns:
            Error result dict
        """
        error_msg = response.get("error", "Unknown error occurred")
        debug_info = ""
        if error_msg == "Unknown error occurred":
            debug_info = f"\n\nFull API response:\n{json.dumps(response, indent=2)}"

        return {"success": False, "error": f"Parameter covariance computation failed: {error_msg}{debug_info}"}

    def _handle_exception(self, e: Exception) -> dict:
        """
        Handle exceptions with enhanced HTTP error parsing.

        Args:
            e: Exception that was raised

        Returns:
            Error result dict with detailed troubleshooting
        """
        error_msg = str(e)
        if isinstance(e, httpx.HTTPStatusError):
            try:
                error_body = e.response.json()
                error_msg = error_body["detail"] if "detail" in error_body else str(error_body)
            except Exception:
                error_msg = e.response.text if hasattr(e.response, "text") else str(e)

        error_details = f"""Parameter covariance computation failed: {error_msg}

Troubleshooting:
- Ensure parameters match those from fit_model call
- Use same data file and mappings as in fitting
- Provide realistic noise variance from residuals
- Verify all required fields are provided
- Check that all units are valid pint units (e.g., "1/volt" not "dimensionless" for inverse volts)

Variance can be estimated from final_loss: variance ≈ final_loss (for MSE)
"""
        return {"success": False, "error": error_details}
