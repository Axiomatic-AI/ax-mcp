# ruff: noqa

"""AxModelFitter server using the Axiomatic API.

This server provides tools for fitting custom mathematical models to experimental data
using the Axiomatic AI platform's optimization API. It includes comprehensive
guidance, examples, and validation to help LLMs use the API correctly.
"""

import json
from typing import Annotated

import numpy as np
from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from axiomatic_mcp.servers.axmodelfitter.information_criteria.formatting import format_aic_bic_results, format_ic_error
from axiomatic_mcp.servers.axmodelfitter.information_criteria.information_criteria import *
from axiomatic_mcp.servers.axmodelfitter.templates.ODE_system_example import ODE_SYSTEM_TEMPLATE
from axiomatic_mcp.servers.axmodelfitter.templates.analytical_complex_ring import ANALYTICAL_COMPLEX_RING_TEMPLATE
from axiomatic_mcp.servers.axmodelfitter.templates.analytical_exponential import ANALYTICAL_EXPONENTIAL_TEMPLATE
from axiomatic_mcp.servers.axmodelfitter.templates.analytical_multivariate import ANALYTICAL_MULTIVARIATE_TEMPLATE
from axiomatic_mcp.servers.axmodelfitter.templates.analytical_polynomial import ANALYTICAL_POLYNOMIAL_TEMPLATE
from axiomatic_mcp.servers.axmodelfitter.templates.analytical_trigonometric import ANALYTICAL_TRIGONOMETRIC_TEMPLATE
from axiomatic_mcp.servers.axmodelfitter.templates.workflow_prompt import WORKFLOW_PROMPT

from ...providers.middleware_provider import get_mcp_middleware
from ...shared import AxiomaticAPIClient
from .data_file_utils import resolve_data_input, resolve_output_data_only
from .services import CovarianceService


def validate_optimization_inputs(input_data: list, output_data: dict, parameters: list, bounds: list, constants: list | None = None):
    """Validate optimization inputs and return extracted names and data info.

    Returns:
        tuple: (input_names, const_names, param_names, bounds_names, N)

    Raises:
        ValueError: If validation fails
    """
    input_names = [in_data["name"] for in_data in input_data]
    const_names = [const["name"] for const in constants] if constants else []
    param_names = [param["name"] for param in parameters]
    bounds_names = [bound["name"] for bound in bounds]

    n = len(output_data["magnitudes"])
    if n == 0:
        raise ValueError("No data points provided. Please provide output data.")

    for in_data in input_data:
        if len(in_data["magnitudes"]) != n:
            raise ValueError(
                f"Input data {in_data['name']} must have the same number of data points as output data: {n}. "
                f"Input data: {input_data}. Output data: {output_data}."
            )

    # Make sure all parameters have bounds
    for var in param_names:
        if var not in bounds_names:
            raise ValueError(f"Parameter {var} has no bounds. Please add bounds.")

    return input_names, const_names, param_names, bounds_names, n


def prepare_bounds_for_optimization(bounds: list, input_names: list, const_names: list, output_name: str):
    """Prepare bounds by setting input/output/constant bounds to ±inf and validating ranges.

    Args:
        bounds: List of bound dictionaries to modify in-place
        input_names: List of input variable names
        const_names: List of constant names
        output_name: Name of output variable

    Raises:
        ValueError: If lower bound > upper bound
    """
    myinf = 1e30

    for var in bounds:
        if var["lower"]["magnitude"] > var["upper"]["magnitude"]:
            raise ValueError(
                f"Lower bound for {var['name']} is greater than upper bound. "
                f"Lower bound: {var['lower']['magnitude']}, Upper bound: {var['upper']['magnitude']}."
            )

        # Set input, output, and constant bounds to -inf to inf for robustness
        if var["name"] in input_names or var["name"] in const_names or var["name"] == output_name:
            var["lower"]["magnitude"] = -myinf
            var["upper"]["magnitude"] = myinf


def check_initial_guess_consistency(parameters: list, bounds: list):
    """Check if initial guesses are within bounds."""
    for param in parameters:
        param_name = param["name"]
        bound = next((bound for bound in bounds if bound["name"] == param_name), None)
        if bound is None:
            raise ValueError(f"Parameter {param_name} has no bounds. Please add bounds.")
        if param["value"]["magnitude"] < bound["lower"]["magnitude"] or param["value"]["magnitude"] > bound["upper"]["magnitude"]:
            raise ValueError(
                f"""Initial guess for {param_name} is not within bounds:
- Initial guess: {param["value"]["magnitude"]}
- Lower bound: {bound["lower"]["magnitude"]}
- Upper bound: {bound["upper"]["magnitude"]}
Adjust the initial guess!"""
            )


def compute_r_squared_from_mse_and_data(mse: float, output_magnitudes: list):
    """Compute R-squared from MSE and output data.

    Args:
        mse: Mean squared error
        output_magnitudes: List of output values (1D or 2D)

    Returns:
        float: R-squared value
    """
    # Convert to numpy array and handle both 1D and 2D cases
    y_true = np.array(output_magnitudes)

    # Flatten to handle multidimensional data consistently
    y_flat = y_true.flatten()
    n_total_elements = len(y_flat)

    if n_total_elements == 0:
        return float("nan")

    if mse < 0:
        return float("nan")

    # For multidimensional data, MSE is already the mean across all elements
    # So SS_res = MSE * total_number_of_elements
    ss_res = mse * n_total_elements

    # Calculate total sum of squares (variance around mean across all dimensions)
    y_mean = np.mean(y_flat)
    ss_tot = np.sum((y_flat - y_mean) ** 2)

    # Handle edge case where all output values are the same
    if ss_tot == 0:
        return 1.0 if mse == 0 else float("-inf")
    else:
        return 1 - ss_res / ss_tot




def evaluate_model(payload: dict) -> dict:
    """Evaluate/predict outputs of a model using the provided payload.

    Args:
        payload: Complete request payload for the model evaluation API

    Returns:
        Dict with predicted outputs and any other response fields

    Raises:
        Exception: If API call fails
    """
    with AxiomaticAPIClient() as client:
        response = client.post("/digital-twin/custom_predict", data=payload)

    return response


mcp = FastMCP(
    name="AxModelFitter Server",
    instructions="""This server provides mathematical model fitting capabilities using the Axiomatic AI platform.

    Fitting Workflow - FOLLOW THESE STEPS:

    1️⃣ DEFINE YOUR MATHEMATICAL MODEL
    Write your model as a JAX function using jnp operations:
    ```python
    def output_variable_name(input_var, param1, param2, ...):
        return param1 * jnp.exp(-param2 * input_var) + param3
    ```

    2️⃣ GET TEMPLATES
    Use `get_fitting_examples` to see working templates:
    • Analytical functions (exponential, polynomial, trigonometric)
    • ODE systems (population dynamics, chemical kinetics)

    3️⃣ ADAPT THE TEMPLATE
    • Replace function with your model
    • Update parameter names and initial guesses
    • Set realistic bounds for ALL parameters, inputs, AND outputs
    • Use proper pint units ('dimensionless', 'nanometer', 'volt', etc.)

    4️⃣ STRUCTURE DATA
    Format input/output data:
    ```python
    input_data = [{"name": "time", "unit": "second", "magnitudes": [0, 1, 2, ...]}, ...]
    output_data = {"name": "concentration", "unit": "molar", "magnitudes": [1.0, 0.8, ...]}}
    ```

    5️⃣ RUN OPTIMIZATION
    Use `fit_model` with your adapted template.

    For detailed guidance, use the `get_workflow_prompt` prompt.

    CRITICAL REQUIREMENTS for all function calls:
    1. ALL functions must use JAX operations: jnp.exp, jnp.sin, jnp.cos, jnp.sqrt, etc.
    2. ALL units must be valid pint units: 'dimensionless', 'nanometer', 'volt', 'second', etc.
    3. ALL parameters, constants, inputs, and outputs need bounds defined
    4. Bounds must include input variables AND output variables

    SUPPORTED FEATURES:
    • Custom JAX function optimization with automatic differentiation
    • Multiple optimizers: nlopt (default, best), scipy (curve_fit), nevergrad (global, gradient-free)
    • Cost functions: mse (default), mae, huber, relative_mse
    • JIT compilation for performance (enabled by default)
    • Unit-aware optimization with automatic conversions
    • Parameter bounds and constraints

    COMMON PINT UNITS:
    • Dimensionless: 'dimensionless' (required for ratios, quality factors, etc.)
    • Length: 'nanometer', 'micrometer', 'meter'
    • Time: 'second', 'millisecond', 'nanosecond'
    • Frequency: 'hertz', 'gigahertz', 'terahertz'
    • Electrical: 'volt', 'ampere', 'ohm', 'watt'
    • Optical: 'nanometer' for wavelength, 'dimensionless' for transmission/reflection

    OPTIMIZER GUIDANCE:
    • nlopt: Best for most cases, uses gradients, very fast convergence
    • scipy: Good for simple curve fitting, uses Levenberg-Marquardt
    • nevergrad: Gradient-free. Can handle integer variables.

    COST FUNCTION GUIDANCE:
    • mse: Standard choice, assumes Gaussian noise
    • mae: More robust to outliers than MSE
    • huber: Combines MSE and MAE benefits, good for mixed noise
    • relative_mse: Good when data spans several orders of magnitude
    """,
    version="0.0.1",
    middleware=get_mcp_middleware(),
)


@mcp.tool(
    name="fit_model",
    description="""Fit a custom JAX mathematical model against experimental data.

    This tool fits user-defined mathematical models to data using numerical optimization.
    All data MUST be provided via files (CSV, Excel, JSON, Parquet) - no direct data input.

    REQUIRED INPUTS:
    1. data_file: Path to your data file (e.g., "/path/to/data.csv")
    2. input_data: Maps file columns to input variables
    3. output_data: Maps file columns to output variables
    4. function_source: JAX function code using jnp operations
    5. parameters: Initial parameter guesses with units
    6. bounds: Bounds for ALL parameters, inputs, and outputs

    DATA MAPPING EXAMPLE:
    - data_file: "/Users/data/experiment.csv"
    - input_data: [{"column": "time_col", "name": "t", "unit": "second"}]
    - output_data: {"columns": ["voltage"], "name": "v", "unit": "volt"}

    FUNCTION REQUIREMENTS:
    - MUST use JAX operations: jnp.exp(-rate*t), jnp.sin(freq*t), jnp.sqrt(x)
    - Valid pint units: 'dimensionless', 'second', 'volt', 'meter', etc.
    - All variables (parameters, inputs, outputs) need bounds

    RETURNS: Optimized parameters, R², execution time, and result files
    """,
    tags=["parameter_estimation", "model_fitting", "curve_fitting", "digital_twin", "jax", "optimization"],
)
async def fit_model(
    # Required parameters first
    model_name: Annotated[str, "Model name (e.g., 'ExponentialDecay', 'RingResonator')"],
    function_source: Annotated[str, "JAX function source code. MUST use jnp operations: jnp.exp, jnp.sin, etc."],
    function_name: Annotated[str, "Function name that computes the model output"],
    parameters: Annotated[list, "Initial parameter guesses: [{'name': 'a', 'value': {'magnitude': 2.0, 'unit': 'dimensionless'}}]"],
    bounds: Annotated[
        list,
        "ALL parameter/input/output bounds: [{'name': 'a', 'lower': {'magnitude': 0, 'unit': 'dimensionless'}, 'upper': {'magnitude': 10, 'unit': 'dimensionless'}}]",
    ],
    # File-based data input (REQUIRED)
    data_file: Annotated[str, "Path to data file (CSV, Excel, JSON, Parquet). All data must be provided via file."],
    input_data: Annotated[
        list, "Input column mappings: [{'column': 'time', 'name': 't', 'unit': 'second'}, {'column': 'x_col', 'name': 'x', 'unit': 'meter'}]"
    ],
    output_data: Annotated[
        dict, "Output column mapping: {'columns': ['signal'], 'name': 'y', 'unit': 'volt'} OR {'columns': ['y1', 'y2'], 'name': 'y', 'unit': 'volt'}"
    ],
    file_format: Annotated[str | None, "File format: 'csv', 'excel', 'json', 'parquet' (auto-detect if None)"] = None,
    # Optional parameters with defaults
    constants: Annotated[list | None, "Fixed constants: [{'name': 'c', 'value': {'magnitude': 3.0, 'unit': 'meter'}}]"] = None,
    docstring: Annotated[str, "Brief description of the model"] = "",
    optimizer_type: Annotated[str, "Optimizer: 'nlopt' (best default), 'scipy' (simple), 'nevergrad' (gradient-free)"] = "nlopt",
    cost_function_type: Annotated[str, "Cost function: 'mse' (default), 'mae', 'huber (with delta=1.0)', 'relative_mse'"] = "mse",
    max_time: Annotated[int, "Maximum optimization time in seconds"] = 5,
    jit_compile: Annotated[bool, "Enable JIT compilation for performance"] = True,
    optimizer_config: Annotated[dict | None, "Optimizer config: {'use_gradient': True, 'tol': 1e-6, 'max_function_eval': 1000000}"] = None,
) -> ToolResult:
    """Fit a model against data using the Axiomatic AI platform."""

    try:
        # Resolve data input from file only
        if data_file is None:
            raise ValueError("data_file is required. All data must be provided via file.")
        if input_data is None:
            raise ValueError("input_data is required when using file-based input.")
        if output_data is None:
            raise ValueError("output_data is required when using file-based input.")

        resolved_input_data, resolved_output_data = resolve_data_input(
            data_file=data_file, input_data=input_data, output_data=output_data, file_format=file_format
        )

        # Validate inputs using helper function
        input_names, const_names, param_names, bounds_names, n = validate_optimization_inputs(
            resolved_input_data, resolved_output_data, parameters, bounds, constants
        )

        # Prepare bounds using helper function
        prepare_bounds_for_optimization(bounds, input_names, const_names, resolved_output_data["name"])
        check_initial_guess_consistency(parameters, bounds)

    except ValueError as e:
        return ToolResult(content=[TextContent(type="text", text=str(e))])

    # Build API request exactly matching the expected format
    if optimizer_config is None:
        optimizer_config = {}
    if constants is None:
        constants = []
    request_data = {
        "model_name": model_name,
        "parameters": parameters,
        "bounds": bounds,
        "constants": constants,
        "input": resolved_input_data,
        "target": resolved_output_data,
        "function_source": function_source,
        "function_name": function_name,
        "docstring": docstring,
        "jit_compile": jit_compile,
        "max_time": max_time,
        "optimizer_type": optimizer_type,
        "cost_function_type": cost_function_type,
        "optimizer_config": optimizer_config or {},
    }

    try:
        # Call the API
        with AxiomaticAPIClient() as client:
            response = client.post("/digital-twin/custom_optimize", data=request_data)

        # Format results
        success = response.get("success", False)
        final_loss = response.get("final_loss")
        execution_time = response.get("execution_time")
        n_evals = response.get("n_evals")

        # Format values safely
        final_loss_str = f"{final_loss:.6e}" if final_loss is not None else "N/A"
        execution_time_str = f"{execution_time:.2f}s" if execution_time is not None else "N/A"

        result_text = f"""# {model_name} Optimization Results

{"✅ **SUCCESS**" if success else "❌ **FAILED**"}

## Performance Metrics
- **Final Loss:** {final_loss_str}
- **Execution Time:** {execution_time_str}
- **Function Evaluations:** {n_evals or "N/A"}
- **Optimizer:** {optimizer_type}
- **Cost Function:** {cost_function_type}

## Optimized Parameters
"""

        optimized_params = {}
        for param in response.get("parameters", []):
            name = param["name"]
            value = param["value"]["magnitude"]
            unit = param["value"]["unit"]
            result_text += f"- **{name}:** {value:.6g} {unit}\n"
            optimized_params[name] = value

        # Warnings
        near_lower = response.get("near_lower", [])
        near_upper = response.get("near_upper", [])
        if near_lower or near_upper:
            result_text += "\n## ⚠️ Parameter Warnings\n"
            if near_lower:
                result_text += f"- **Near Lower Bounds:** {', '.join(near_lower)}\n"
            if near_upper:
                result_text += f"- **Near Upper Bounds:** {', '.join(near_upper)}\n"
            result_text += "\n*Consider adjusting bounds if unexpected.*\n"

        return ToolResult(content=[TextContent(type="text", text=result_text)])

    except Exception as e:
        error_details = f"""❌ **Optimization Failed**

**Error:** {e!s}

## Troubleshooting Tips:

1. **Check JAX Functions:** Ensure you use `jnp.exp()`, `jnp.sin()`, etc.
2. **Verify Units:** Use valid pint units like 'dimensionless', 'nanometer', 'volt'
3. **Parameter Bounds:** All parameters need lower/upper bounds
4. **Input/Output Bounds:** Input and output variables need bounds too
5. **Data Alignment:** Input and output data should have same length

## Need Help? Try the example tool:
Use `get_fitting_examples` to see working examples.
"""
        return ToolResult(content=[TextContent(type="text", text=error_details)])


@mcp.prompt(
    name="get_workflow_prompt",
    description="Step-by-step guide for model fitting with the AxModelFitter. Shows complete workflow from model definition to optimization execution.",
)
def get_workflow_prompt() -> str:
    """Generate a generic optimization workflow guide."""
    return WORKFLOW_PROMPT


@mcp.tool(
    name="get_fitting_examples",
    description="""Get complete working examples for model fitting with the AxModelFitter.

    Returns ready-to-use templates with:
    - Proper JAX function syntax
    - Correct pint units
    - Realistic parameter bounds
    - File-based data structure examples

    Use these as starting points - copy the structure and modify for your specific model.
    Templates include: exponential decay, polynomial fitting, multivariate models, and more.
    """,
    tags=["examples", "tutorial", "templates"],
)
async def get_fitting_examples() -> ToolResult:
    """Get clean JSON examples ready to use with fit_model."""

    # Generic templates covering different model categories
    templates = {
        "analytical_exponential": ANALYTICAL_EXPONENTIAL_TEMPLATE,
        "analytical_polynomial": ANALYTICAL_POLYNOMIAL_TEMPLATE,
        "analytical_multivariate": ANALYTICAL_MULTIVARIATE_TEMPLATE,
        "analytical_trigonometric": ANALYTICAL_TRIGONOMETRIC_TEMPLATE,
        "ODE_system_example": ODE_SYSTEM_TEMPLATE,
        "analytical_complex_ring": ANALYTICAL_COMPLEX_RING_TEMPLATE,
    }

    # Concise template overview for LLMs
    template_summary = {}
    for key, template in templates.items():
        template_summary[key] = {
            "category": template["category"],
            "description": template["description"],
            "function": template["function_source"],  # Just the function signature
            "parameters": len(template["parameters"]),
            "use_cases": template["description"].split(" - ")[1] if " - " in template["description"] else "General modeling",
            "optimizer_type": template["optimizer_type"],
            "cost_function_type": template["cost_function_type"],
            "max_time": template["max_time"],
            "jit_compile": template["jit_compile"],
            "optimizer_config": template["optimizer_config"],
        }

    summary_text = f"""# fit Templates

## Available Template Categories:

** Analytical Functions:**
• `analytical_exponential` - Exponential decay/growth models
• `analytical_polynomial` - Polynomial/quadratic functions
• `analytical_trigonometric` - Sinusoidal/periodic signals

## How to Use:
1. **Pick a template** closest to your model structure
2. **Replace the function** with your mathematical model
3. **Update parameters** and bounds for your system
4. **Replace data** with your experimental measurements
5. **Run optimization** with `fit_model`

## Template Details:
{json.dumps(template_summary, indent=2)}

Use `get_workflow_prompt` prompt for detailed step-by-step guidance!
All templates are generic - adapt the function, parameters, and data to your specific model."""

    return ToolResult(
        content=[TextContent(type="text", text=summary_text)],
        structured_content={"templates": templates},
    )


@mcp.tool(
    name="calculate_information_criteria",
    description="""Calculate AIC and BIC information criteria for model selection.

    REQUIRED INPUTS:
    - loss_value: MSE or MAE value from your optimization
    - cost_function_type: Either 'mse' or 'mae' only
    - n_parameters: Number of fitted parameters in your model
    - sigma: Noise standard deviation (REQUIRED for MSE, None for MAE)
    - data_file: Path to your data file
    - output_data: Which columns contain your output data

    WHEN TO USE:
    - Compare different model architectures (linear vs exponential vs polynomial)
    - Select best model complexity (avoid overfitting)
    - Use AIC/BIC values: lower is better

    SIGMA PARAMETER:
    - For MSE (Gaussian noise): Provide noise std dev from domain knowledge
    - For MAE (Laplace noise): Set sigma to None
    - Example: experimental measurement error ±0.1 volts → sigma=0.1

    RETURNS: AIC, BIC, AICc values with interpretable model comparison metrics.
    """,
    tags=["statistics", "model_selection", "information_criteria", "bayesian"],
)
async def calculate_information_criteria(
    loss_value: Annotated[float, "Mean loss value from optimization (MSE or MAE only)"],
    cost_function_type: Annotated[str, "Loss function type: 'mse' (Gaussian) or 'mae' (Laplace) only"],
    n_parameters: Annotated[int, "Number of fitted parameters in mean function (scale param added automatically)"],
    sigma: Annotated[
        float | str | None,
        "REQUIRED noise std dev for diagonal covariance Σ=σ²I. Specify from domain knowledge or estimate based on available data.",  # noqa
    ],
    # File-based data input (REQUIRED)
    data_file: Annotated[str, "Path to data file (CSV, Excel, JSON, Parquet). All data must be provided via file."],
    output_data: Annotated[
        dict, "Output column mapping: {'columns': ['y'], 'name': 'y', 'unit': 'volt'} or {'columns': ['y1', 'y2'], 'name': 'y', 'unit': 'volt'}"
    ],
    file_format: Annotated[str | None, "File format: 'csv', 'excel', 'json', 'parquet' (auto-detect if None)"] = None,
    # Other parameters
    include_scale_param: Annotated[bool, "Include scale parameter (σ² or b) in k count"] = False,
    n_obs: Annotated[int | None, "Explicit count of independent residuals. If None, infers from output data"] = None,
    df_effective: Annotated[float | None, "Effective degrees of freedom for penalized models (EXCLUDING scale)"] = None,
    aicc_include_scale: Annotated[bool, "Include scale parameter in AICc correction (literature varies)"] = True,
    n_scale_params: Annotated[int, "Number of scale parameters: 1 for single-output, d for d-output with separate scales"] = 1,
) -> ToolResult:
    """Calculate AIC and BIC information criteria for digital twin model selection."""

    try:
        # Resolve output data from file only
        resolved_output_values = resolve_output_data_only(data_file=data_file, output_data=output_data, file_format=file_format)

        # Handle string-to-float conversion for sigma (JSON might pass it as string)
        if sigma is not None:
            try:
                sigma = float(sigma)
            except Exception as e:
                raise ValueError(f"sigma must be a number. Error: {e!s}") from e

        if n_parameters <= 0:
            raise ValueError("Number of parameters must be positive")

        if len(resolved_output_values) == 0:
            raise ValueError("Output values cannot be empty")

        if loss_value < 0:
            raise ValueError("Loss value cannot be negative")

        if sigma is not None:
            if cost_function_type != "mse":
                raise ValueError("sigma parameter is only supported for 'mse' (Gaussian) cost function")
            if sigma <= 0:
                raise ValueError("sigma must be positive")

            # Warn if sigma and MSE are very inconsistent (suggests different assumptions)
            expected_sigma = np.sqrt(loss_value)  # If MSE = σ², then σ = √MSE  # noqa
            relative_diff = abs(sigma - expected_sigma) / expected_sigma if expected_sigma > 0 else float("inf")
            if relative_diff > 0.5:  # More than 50% difference
                import warnings

                warnings.warn(
                    f"sigma={sigma:.6f} differs significantly from √MSE={expected_sigma:.6f}. "
                    f"This may indicate different noise assumptions. Consider if your sigma "
                    f"represents the true noise level vs. the empirical fit quality.",
                    stacklevel=2,
                )

        # Use helper function for AIC/BIC calculation
        result = compute_aic_bic_from_loss_and_data(
            loss_value,
            cost_function_type,
            resolved_output_values,
            n_parameters,
            sigma,
            include_scale_param,
            n_obs,
            df_effective,
            aicc_include_scale,
            n_scale_params,
        )

        # Extract values for display
        aic = result["aic"]
        bic = result["bic"]
        aicc = result["aicc"]
        scale_est = result["scale_est"]
        k_effective = result["k_effective"]
        n_total = result["n_total"]
        log_likelihood_est = result["log_likelihood_est"]
        delta_bic_aic = result["delta_bic_aic"]
        assumes_independence = result["assumes_independence"]

        # Format conditional values to avoid f-string errors
        aicc_str = f"{aicc:.2f}" if np.isfinite(aicc) else "Infinite (over-parameterized)"

        # Scale parameter label and sigma information
        if cost_function_type == "mse":
            scale_label = f"User-provided σ = {sigma:.6f} (diagonal covariance Σ = σ²I)"  # noqa
            likelihood_method = "General Gaussian likelihood with user-provided σ"  # noqa
        else:  # MAE
            scale_label = "Scale estimate (b for Laplace)"
            likelihood_method = "Laplace likelihood with estimated scale parameter"

        result_text = format_aic_bic_results(
            aic=aic,
            bic=bic,
            aicc_str=aicc_str,
            delta_bic_aic=delta_bic_aic,
            scale_label=scale_label,
            scale_est=scale_est,
            log_likelihood_est=log_likelihood_est,
            likelihood_method=likelihood_method,
            cost_function_type=cost_function_type,
            loss_value=loss_value,
            k_effective=k_effective,
            n_total=n_total,
            assumes_independence=assumes_independence,
            df_effective=df_effective,
            n_parameters=n_parameters,
            include_scale_param=include_scale_param,
            aicc_include_scale=aicc_include_scale,
            n_obs=n_obs,
        )

        return ToolResult(
            content=[TextContent(type="text", text=result_text)],
            structured_content={
                "aic": result["aic"],
                "bic": result["bic"],
                "aicc": result["aicc"],
                "k_effective": result["k_effective"],
                "n_total": result["n_total"],
                "log_likelihood_est": result["log_likelihood_est"],
                "scale_est": result["scale_est"],
                "delta_bic_aic": result["delta_bic_aic"],
                "assumes_independence": result["assumes_independence"],
            },
        )

    except Exception as e:
        return ToolResult(content=[TextContent(type="text", text=format_ic_error(e))])


@mcp.tool(
    name="calculate_r_squared",
    description="""Calculate R-squared to measure how well your model fits the data.

    SIMPLE USAGE:
    - mse: The MSE value from your optimization result
    - data_file: Path to your original data file
    - output_data: Which columns contain your measured values

    WHAT R² MEANS:
    - R² = 1.0: Perfect fit (model explains 100% of variance)
    - R² = 0.8: Good fit (model explains 80% of variance)
    - R² = 0.0: Poor fit (model no better than just using the mean)
    - R² < 0.0: Very poor fit (model worse than just using the mean)

    WORKS WITH:
    - Single output: output_data = {"columns": ["voltage"], "name": "v", "unit": "volt"}
    - Multiple outputs: output_data = {"columns": ["x", "y"], "name": "position", "unit": "meter"}

    Use this to quickly assess if your optimization produced a good fit.
    """,
    tags=["statistics", "model_evaluation", "goodness_of_fit"],
)
async def calculate_r_squared(
    mse: Annotated[float, "Mean squared error from the optimization"],
    # File-based data input (REQUIRED)
    data_file: Annotated[str, "Path to data file (CSV, Excel, JSON, Parquet). All data must be provided via file."],
    output_data: Annotated[
        dict, "Output column mapping: {'columns': ['y'], 'name': 'y', 'unit': 'volt'} or {'columns': ['y1', 'y2'], 'name': 'y', 'unit': 'volt'}"
    ],
    file_format: Annotated[str | None, "File format: 'csv', 'excel', 'json', 'parquet' (auto-detect if None)"] = None,
) -> ToolResult:
    """Calculate R-squared coefficient of determination for 1D or multidimensional data."""

    try:
        # Resolve output data from file only
        resolved_output_values = resolve_output_data_only(data_file=data_file, output_data=output_data, file_format=file_format)

        if len(resolved_output_values) == 0:
            raise ValueError("Output values cannot be empty")

        if mse < 0:
            raise ValueError("MSE cannot be negative")

        # Use helper function for R² calculation
        r_squared = compute_r_squared_from_mse_and_data(mse, resolved_output_values)

        # Get data info for display
        y_true = np.array(resolved_output_values)
        n_total_elements = len(y_true.flatten())

        # Determine data structure for display
        data_shape = y_true.shape
        if len(data_shape) == 1:
            data_info = f"1D data with {data_shape[0]} samples"
        else:
            data_info = f"Multidimensional data: {data_shape[0]} samples x {data_shape[1]} dimensions"

        # Format result
        result_text = f"""# R-squared Calculation Results

## Model Fit Quality
- **R² Value:** {r_squared:.6f}
- **MSE:** {mse:.6e}
- **Data Structure:** {data_info}
- **Total Elements:** {n_total_elements}

## Interpretation
"""

        if r_squared >= 0.9:
            result_text += "- **Excellent fit** (R² ≥ 0.9) - Model explains >90% of variance"
        elif r_squared >= 0.7:
            result_text += "- **Good fit** (0.7 ≤ R² < 0.9) - Model explains 70-90% of variance"
        elif r_squared >= 0.5:
            result_text += "- **Moderate fit** (0.5 ≤ R² < 0.7) - Model explains 50-70% of variance"
        elif r_squared >= 0.0:
            result_text += "- **Poor fit** (0.0 ≤ R² < 0.5) - Model explains <50% of variance"
        else:
            result_text += "- **Very poor fit** (R² < 0.0) - Model worse than simply using the mean"

        result_text += f"\n- **Variance explained:** {r_squared * 100:.2f}%" if r_squared >= 0 else ""

        return ToolResult(content=[TextContent(type="text", text=result_text)])

    except Exception as e:
        error_text = f"""❌ **R-squared Calculation Failed**

**Error:** {e!s}

## Troubleshooting:
- Ensure MSE is a positive number
- Verify output data is properly specified in data file
- For multidimensional data: [[sample1_dim1, sample1_dim2], [sample2_dim1, sample2_dim2], ...]
- Check that output data matches what was used in optimization
"""
        return ToolResult(content=[TextContent(type="text", text=error_text)])


@mcp.tool(
    name="cross_validate_model",
    description="""Test how well your model generalizes to new data using cross-validation.

    REQUIRED INPUTS (same as fit_model):
    - All model parameters: function_source, parameters, bounds, etc.
    - data_file: Path to your data file
    - input_data: Maps file columns to input variables
    - output_data: Maps file columns to output variables

    VALIDATION TYPES:
    - 'kfold': Split data into equal parts (good default)
    - 'shuffle': Random train/test splits
    - 'custom': Specify your own train/test indices

    TYPICAL USAGE:
    1. Use same parameters as your fit_model call
    2. Set validation_strategy='kfold' and n_splits=5
    3. Check if test R² values are consistent across folds

    INTERPRETATION:
    - Consistent high R² across folds: Good generalization
    - Large R² variation: Model may be overfitting
    - Low average R²: Model not capturing data patterns well
    """,
    tags=["validation", "cross_validation", "model_evaluation", "statistics"],
)
async def cross_validate_model(
    # Model definition parameters
    model_name: Annotated[str, "Model name for identification"],
    function_source: Annotated[str, "JAX function source code using jnp operations"],
    function_name: Annotated[str, "Function name that computes the model output"],
    initial_parameters: Annotated[list, "Initial parameter guesses for optimization on each fold"],
    bounds: Annotated[list, "Parameter/input/output bounds"],
    # File-based data input (REQUIRED)
    data_file: Annotated[str, "Path to data file (CSV, Excel, JSON, Parquet). All data must be provided via file."],
    input_data: Annotated[
        list, "Input column mappings: [{'column': 'time', 'name': 't', 'unit': 'second'}, {'column': 'x_col', 'name': 'x', 'unit': 'meter'}]"
    ],
    output_data: Annotated[
        dict, "Output column mapping: {'columns': ['signal'], 'name': 'y', 'unit': 'volt'} OR {'columns': ['y1', 'y2'], 'name': 'y', 'unit': 'volt'}"
    ],
    file_format: Annotated[str | None, "File format: 'csv', 'excel', 'json', 'parquet' (auto-detect if None)"] = None,
    constants: Annotated[list | None, "Fixed constants"] = None,
    # Validation strategy
    validation_strategy: Annotated[str, "Validation type: 'kfold', 'shuffle', or 'custom'"] = "kfold",
    n_splits: Annotated[int, "Number of validation folds (for kfold and shuffle)"] = 5,
    test_size: Annotated[float, "Test set proportion (for shuffle split)"] = 0.2,
    random_state: Annotated[int | None, "Random seed for reproducibility"] = 31415926,
    custom_splits: Annotated[list | None, "Custom train/test splits: [{'train': [0,1,2], 'test': [3,4]}, ...]"] = None,
    # Optimization settings
    cost_function_type: Annotated[str, "Cost function: 'mse', 'mae', 'huber', 'relative_mse'"] = "mse",
    jit_compile: Annotated[bool, "Enable JIT compilation"] = True,
    optimizer_type: Annotated[str, "Optimizer: 'nlopt' (best default), 'scipy' (simple), 'nevergrad' (gradient-free)"] = "nlopt",
    max_time: Annotated[int, "Maximum optimization time in seconds per fold"] = 5,
    optimizer_config: Annotated[dict | None, "Optimizer config: {'use_gradient': True, 'tol': 1e-6, 'max_function_eval': 1000000}"] = None,
) -> ToolResult:
    """Perform cross-validation on model."""

    try:
        # Resolve data input from file only
        resolved_input_data, resolved_output_data = resolve_data_input(
            data_file=data_file, input_data=input_data, output_data=output_data, file_format=file_format
        )

        # Import scikit-learn here to avoid dependency if not used
        from sklearn.model_selection import KFold, ShuffleSplit

        # Get data dimensions
        n_samples = len(resolved_output_data["magnitudes"])

        # Create cross-validation splits - sklearn can work directly with n_samples
        splits = []

        if validation_strategy == "kfold":
            cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
            # cv.split() just needs any array-like of length n_samples
            splits = list(cv.split(range(n_samples)))
            strategy_desc = f"KFold with {n_splits} folds"

        elif validation_strategy == "shuffle":
            cv = ShuffleSplit(n_splits=n_splits, test_size=test_size, random_state=random_state)
            splits = list(cv.split(range(n_samples)))
            strategy_desc = f"ShuffleSplit with {n_splits} splits, test_size={test_size}"

        elif validation_strategy == "custom":
            if custom_splits is None:
                return ToolResult(content=[TextContent(type="text", text="Custom splits must be provided when using 'custom' validation strategy.")])

            # Convert custom splits to train/test index lists
            for split in custom_splits:
                if "train" not in split or "test" not in split:
                    return ToolResult(
                        content=[TextContent(type="text", text="Each custom split must have 'train' and 'test' keys with index lists.")]
                    )
                splits.append((split["train"], split["test"]))
            strategy_desc = f"Custom splits with {len(splits)} folds"

        else:
            return ToolResult(content=[TextContent(type="text", text="validation_strategy must be 'kfold', 'shuffle', or 'custom'.")])

        if len(splits) == 0:
            return ToolResult(content=[TextContent(type="text", text="No validation splits generated. Check your parameters.")])

        # Prepare results storage
        fold_results = []
        test_losses = []
        test_r2s = []

        # Process each fold
        for fold_idx, (train_indices, test_indices) in enumerate(splits):
            try:
                # Create train data for this fold
                train_input_data = []
                for inp in resolved_input_data:
                    train_magnitudes = [inp["magnitudes"][i] for i in train_indices]
                    train_input_data.append({"name": inp["name"], "unit": inp["unit"], "magnitudes": train_magnitudes})

                train_output_magnitudes = [resolved_output_data["magnitudes"][i] for i in train_indices]
                train_output_data = {
                    "name": resolved_output_data["name"],
                    "unit": resolved_output_data["unit"],
                    "magnitudes": train_output_magnitudes,
                }

                # Validate training data and prepare bounds using helper functions
                try:
                    input_names, const_names, param_names, bounds_names, train_n = validate_optimization_inputs(
                        train_input_data, train_output_data, initial_parameters, bounds, constants
                    )

                    # Make copy of bounds to avoid modifying original
                    fold_bounds = []
                    for bound in bounds:
                        fold_bound = {
                            "name": bound["name"],
                            "lower": {"magnitude": bound["lower"]["magnitude"], "unit": bound["lower"]["unit"]},
                            "upper": {"magnitude": bound["upper"]["magnitude"], "unit": bound["upper"]["unit"]},
                        }
                        fold_bounds.append(fold_bound)

                    # Prepare bounds for this fold
                    prepare_bounds_for_optimization(fold_bounds, input_names, const_names, train_output_data["name"])

                except ValueError as validation_error:
                    fold_results.append(
                        {
                            "fold": fold_idx + 1,
                            "train_size": len(train_indices),
                            "test_size": len(test_indices),
                            "test_loss": "Failed",
                            "test_r2": "Failed",
                            "error": f"Validation failed: {validation_error}",
                        }
                    )
                    continue

                # Build optimization request for train data
                train_payload = {
                    "model_name": f"{model_name}_fold_{fold_idx + 1}",
                    "parameters": initial_parameters,
                    "bounds": fold_bounds,
                    "constants": constants or [],
                    "input": train_input_data,
                    "target": train_output_data,
                    "function_source": function_source,
                    "function_name": function_name,
                    "docstring": f"Cross-validation training fold {fold_idx + 1}",
                    "jit_compile": jit_compile,
                    "max_time": max_time,
                    "optimizer_type": optimizer_type,
                    "cost_function_type": cost_function_type,
                    "optimizer_config": optimizer_config or {},
                }

                # Optimize model on training data
                with AxiomaticAPIClient() as client:
                    train_response = client.post("/digital-twin/custom_optimize", data=train_payload)

                # Check if optimization succeeded
                if not train_response.get("success", False):
                    fold_results.append(
                        {
                            "fold": fold_idx + 1,
                            "train_size": len(train_indices),
                            "test_size": len(test_indices),
                            "test_loss": "Failed",
                            "test_r2": "Failed",
                            "error": f"Training optimization failed: {train_response.get('error', 'Unknown error')}",
                        }
                    )
                    continue

                # Get optimized parameters from training
                optimized_params = train_response.get("parameters", [])
                if not optimized_params:
                    fold_results.append(
                        {
                            "fold": fold_idx + 1,
                            "train_size": len(train_indices),
                            "test_size": len(test_indices),
                            "test_loss": "Failed",
                            "test_r2": "Failed",
                            "error": "No optimized parameters returned from training",
                        }
                    )
                    continue

                # Create test data for this fold
                test_input_data = []
                for inp in resolved_input_data:
                    test_magnitudes = [inp["magnitudes"][i] for i in test_indices]
                    test_input_data.append({"name": inp["name"], "unit": inp["unit"], "magnitudes": test_magnitudes})

                test_output_magnitudes = [resolved_output_data["magnitudes"][i] for i in test_indices]
                test_output_data = {"name": resolved_output_data["name"], "unit": resolved_output_data["unit"], "magnitudes": test_output_magnitudes}

                # Build payload for loss evaluation on test data using optimized parameters
                loss_payload = {
                    "parameters": optimized_params,
                    "bounds": fold_bounds,
                    "constants": constants or [],
                    "input": test_input_data,
                    "target": test_output_data,
                    "function_source": function_source,
                    "function_name": function_name,
                    "jit_compile": jit_compile,
                    "cost_function_type": cost_function_type,
                }

                # Evaluate loss on test fold
                loss_response = evaluate_loss(loss_payload)
                test_loss = loss_response.get("cost_value")

                if test_loss is None:
                    fold_results.append(
                        {
                            "fold": fold_idx + 1,
                            "train_size": len(train_indices),
                            "test_size": len(test_indices),
                            "test_loss": "Failed",
                            "test_r2": "Failed",
                            "error": "Test loss evaluation failed",
                        }
                    )
                    continue

                # Calculate R² for this fold using helper function
                r2 = compute_r_squared_from_mse_and_data(test_loss, test_output_magnitudes)

                # Store results
                fold_results.append(
                    {
                        "fold": fold_idx + 1,
                        "train_size": len(train_indices),
                        "test_size": len(test_indices),
                        "test_loss": float(test_loss),
                        "test_r2": float(r2),
                    }
                )

                test_losses.append(test_loss)
                test_r2s.append(r2)

            except Exception as fold_error:
                fold_results.append(
                    {
                        "fold": fold_idx + 1,
                        "train_size": len(train_indices),
                        "test_size": len(test_indices),
                        "test_loss": "Failed",
                        "test_r2": "Failed",
                        "error": str(fold_error),
                    }
                )

        # Calculate summary statistics
        valid_losses = [x for x in test_losses if isinstance(x, int | float) and not np.isnan(x)]
        valid_r2s = [x for x in test_r2s if isinstance(x, int | float) and not np.isnan(x)]

        # Format results
        result_text = f"""# Cross-Validation Results: {model_name}

## Validation Strategy
- **Method:** {strategy_desc}
- **Cost Function:** {cost_function_type}
- **Successful Folds:** {len(valid_losses)}/{len(splits)}

## Summary Statistics
"""

        if valid_losses:
            result_text += f"""- **Mean Test Loss:** {np.mean(valid_losses):.6e} ± {np.std(valid_losses):.6e}
- **Mean Test R²:** {np.mean(valid_r2s):.6f} ± {np.std(valid_r2s):.6f}
- **Min Test Loss:** {np.min(valid_losses):.6e}
- **Max Test Loss:** {np.max(valid_losses):.6e}
- **Min Test R²:** {np.min(valid_r2s):.6f}
- **Max Test R²:** {np.max(valid_r2s):.6f}
"""
        else:
            result_text += "- **No successful folds** - All validation attempts failed\n"

        result_text += "\n## Fold-by-Fold Results\n"

        for result in fold_results:
            if isinstance(result["test_loss"], int | float):
                result_text += (
                    f"- **Fold {result['fold']}:** Loss={result['test_loss']:.6e}, "
                    f"R²={result['test_r2']:.6f} (train={result['train_size']}, test={result['test_size']})\n"
                )
            else:
                error_msg = result.get("error", "Unknown error")
                result_text += f"- **Fold {result['fold']}:** ❌ Failed - {error_msg} (train={result['train_size']}, test={result['test_size']})\n"

        # Model assessment
        if valid_r2s:
            mean_r2 = np.mean(valid_r2s)
            result_text += "\n## Model Assessment\n"
            if mean_r2 >= 0.9:
                result_text += "- **Excellent generalization** (Mean R² ≥ 0.9)\n"
            elif mean_r2 >= 0.7:
                result_text += "- **Good generalization** (0.7 ≤ Mean R² < 0.9)\n"
            elif mean_r2 >= 0.5:
                result_text += "- **Moderate generalization** (0.5 ≤ Mean R² < 0.7)\n"
            elif mean_r2 >= 0.0:
                result_text += "- **Poor generalization** (0.0 ≤ Mean R² < 0.5)\n"
            else:
                result_text += "- **Very poor generalization** (Mean R² < 0.0)\n"

            if len(valid_r2s) > 1:
                r2_std = np.std(valid_r2s)
                if r2_std < 0.05:
                    result_text += "- **Consistent performance** across folds (low R² variance)\n"
                elif r2_std > 0.2:
                    result_text += "- **Inconsistent performance** across folds (high R² variance) - possible overfitting\n"

        return ToolResult(
            content=[TextContent(type="text", text=result_text)],
            structured_content={
                "validation_strategy": strategy_desc,
                "fold_results": fold_results,
                "summary": {
                    "mean_test_loss": float(np.mean(valid_losses)) if valid_losses else None,
                    "std_test_loss": float(np.std(valid_losses)) if valid_losses else None,
                    "mean_test_r2": float(np.mean(valid_r2s)) if valid_r2s else None,
                    "std_test_r2": float(np.std(valid_r2s)) if valid_r2s else None,
                    "successful_folds": len(valid_losses),
                    "total_folds": len(splits),
                },
            },
        )

    except ImportError:
        return ToolResult(
            content=[
                TextContent(type="text", text="❌ **Cross-validation failed**: scikit-learn is required. Install with: pip install scikit-learn")
            ]
        )

    except Exception as e:
        error_text = f"""❌ **Cross-validation failed**

**Error:** {e!s}

## Troubleshooting:
- Ensure initial parameters have reasonable starting values
- Check that input/output data have consistent lengths
- For custom splits, provide format: [{{'train': [0,1,2], 'test': [3,4]}}, ...]
- Verify n_splits is appropriate for your data size
- Consider increasing max_time if optimization fails on training folds
"""
        return ToolResult(content=[TextContent(type="text", text=error_text)])


@mcp.tool(
    name="compare_models",
    description="""Compare multiple models to find the best one using statistical criteria.

    USE CASE: You have several competing models (linear, exponential, polynomial) fitted to the same data.
    This tool tells you which model is statistically best.

    REQUIRED INPUTS:
    - models: List of your fitted models with their loss values and parameter counts
    - data_file: Path to your data file (same data used for all models)
    - output_data: Which columns contain your output data
    - sigma: Noise level (required for MSE models, None for MAE models)

    EXAMPLE MODELS INPUT:
    [
        {"name": "Linear", "loss_value": 0.05, "cost_function_type": "mse", "n_parameters": 2},
        {"name": "Exponential", "loss_value": 0.02, "cost_function_type": "mse", "n_parameters": 3}
    ]

    RETURNS: Ranked models with statistical evidence for which is best.
    Lower AIC/BIC = better model. Akaike weights show relative model support.
    """,
    tags=["statistics", "model_selection", "model_comparison", "bayesian"],
)
async def compare_models(
    models: Annotated[
        list,
        "List of model dicts: [{'name': 'Model1', 'loss_value': 0.01, 'cost_function_type': 'mse', 'n_parameters': 3}, ...]",
    ],
    # File-based data input (REQUIRED)
    data_file: Annotated[str, "Path to data file (CSV, Excel, JSON, Parquet). All data must be provided via file."],
    output_data: Annotated[
        dict, "Output column mapping: {'columns': ['y'], 'name': 'y', 'unit': 'volt'} or {'columns': ['y1', 'y2'], 'name': 'y', 'unit': 'volt'}"
    ],
    file_format: Annotated[str | None, "File format: 'csv', 'excel', 'json', 'parquet' (auto-detect if None)"] = None,
    # Other parameters
    sigma: Annotated[
        float | str | None,
        "REQUIRED noise std dev for diagonal covariance Σ=σ²I applied to ALL models. For mse: provide from domain knowledge. For mae: use None.",  # noqa
    ] = None,
    include_scale_param: Annotated[bool, "Include scale parameter (σ² or b) in k count"] = False,
    n_obs: Annotated[int | None, "Explicit count of independent residuals for ALL models. If None, infers from output data"] = None,
    df_effective: Annotated[float | None, "Effective degrees of freedom for penalized models (EXCLUDING scale) - applied to ALL models"] = None,
    aicc_include_scale: Annotated[bool, "Include scale parameter in AICc correction (literature varies)"] = True,
    n_scale_params: Annotated[int, "Number of scale parameters: 1 for single-output, d for d-output with separate scales"] = 1,
) -> ToolResult:
    """Compare multiple models using information criteria for model selection."""

    try:
        # Resolve output data from file first
        resolved_output_values = resolve_output_data_only(data_file=data_file, output_data=output_data, file_format=file_format)

        if sigma is not None:
            try:
                sigma = float(sigma)
            except Exception as e:
                raise ValueError(f"sigma must be a number. Error: {e!s}") from e

        if len(models) < 2:
            return ToolResult(content=[TextContent(type="text", text="At least 2 models are required for comparison.")])

        # Check if any models use MSE - if so, sigma is required
        mse_models = [model.get("cost_function_type") for model in models if model.get("cost_function_type") == "mse"]
        if mse_models and sigma is None:
            error_msg = (
                "❌ **Sigma parameter required**: One or more models use 'mse' cost function, "
                "which requires the sigma parameter for diagonal covariance Σ=σ²I. "  # noqa
                "Provide the noise standard deviation from domain knowledge."
            )
            return ToolResult(content=[TextContent(type="text", text=error_msg)])

        # Calculate AIC/BIC for each model
        model_results = []
        valid_models = []

        for i, model in enumerate(models):
            try:
                # Validate required fields (removed output_values)
                required_fields = ["name", "loss_value", "cost_function_type", "n_parameters"]
                for field in required_fields:
                    if field not in model:
                        raise ValueError(f"Model {i + 1} missing required field: {field}")

                # Calculate information criteria using resolved data
                ic_result = compute_aic_bic_from_loss_and_data(
                    model["loss_value"],
                    model["cost_function_type"],
                    resolved_output_values,
                    model["n_parameters"],
                    sigma,
                    include_scale_param,
                    n_obs,
                    df_effective,
                    aicc_include_scale,
                    n_scale_params,
                )

                model_result = {
                    "name": model["name"],
                    "loss_value": model["loss_value"],
                    "cost_function_type": model["cost_function_type"],
                    "n_parameters": model["n_parameters"],
                    "k_effective": ic_result["k_effective"],
                    "sample_size": ic_result["n_total"],
                    "aic": ic_result["aic"],
                    "bic": ic_result["bic"],
                    "aicc": ic_result["aicc"],
                    "log_likelihood_est": ic_result["log_likelihood_est"],
                    "assumes_independence": ic_result["assumes_independence"],
                }

                model_results.append(model_result)
                if all(np.isfinite([ic_result["aic"], ic_result["bic"]])):
                    valid_models.append(model_result)

            except Exception as e:
                model_results.append({"name": model.get("name", f"Model_{i + 1}"), "error": str(e)})

        if len(valid_models) < 2:
            return ToolResult(
                content=[TextContent(type="text", text="At least 2 valid models are required for comparison after removing failed calculations.")]
            )

        # Find best models
        best_aic_idx = np.argmin([m["aic"] for m in valid_models])
        best_bic_idx = np.argmin([m["bic"] for m in valid_models])

        # Fix AICc index bug - find indices with finite AICc first
        finite_aicc_idxs = [i for i, m in enumerate(valid_models) if np.isfinite(m["aicc"])]
        if finite_aicc_idxs:
            best_aicc_idx = min(finite_aicc_idxs, key=lambda i: valid_models[i]["aicc"])
            best_aicc_model = valid_models[best_aicc_idx]
        else:
            best_aicc_idx = None
            best_aicc_model = None

        best_aic_model = valid_models[best_aic_idx]
        best_bic_model = valid_models[best_bic_idx]

        # Calculate relative information criteria (ΔIC)
        for model in valid_models:
            model["delta_aic"] = model["aic"] - best_aic_model["aic"]
            model["delta_bic"] = model["bic"] - best_bic_model["bic"]
            if best_aicc_model is not None and np.isfinite(model["aicc"]):
                model["delta_aicc"] = model["aicc"] - best_aicc_model["aicc"]
            else:
                model["delta_aicc"] = float("inf")

        # Calculate Akaike weights
        delta_aics = [m["delta_aic"] for m in valid_models]
        exp_terms = [np.exp(-0.5 * delta) for delta in delta_aics]
        sum_exp = sum(exp_terms)

        for i, model in enumerate(valid_models):
            model["akaike_weight"] = exp_terms[i] / sum_exp

        # Sort models by AIC for presentation
        valid_models.sort(key=lambda x: x["aic"])

        # Format results
        result_text = f"""# Model Comparison using Information Criteria

## Best Models by Criterion
- **Best AIC:** {best_aic_model["name"]} (AIC = {best_aic_model["aic"]:.2f})
- **Best BIC:** {best_bic_model["name"]} (BIC = {best_bic_model["bic"]:.2f})"""

        if best_aicc_model is not None:
            result_text += f"\n- **Best AICc:** {best_aicc_model['name']} (AICc = {best_aicc_model['aicc']:.2f})"
        else:
            result_text += "\n- **Best AICc:** No finite AICc values (over-parameterized models)"

        result_text += """

## Model Comparison Table
| Model | Loss | k_eff | n | AIC | BIC | AICc | ΔAIC | ΔBIC | Weight |
|-------|------|-------|---|-----|-----|------|------|------|--------|"""

        for model in valid_models:
            weight_str = f"{model['akaike_weight']:.3f}"
            delta_aic_str = f"{model['delta_aic']:.2f}" if model["delta_aic"] < 1000 else f"{model['delta_aic']:.1e}"
            delta_bic_str = f"{model['delta_bic']:.2f}" if model["delta_bic"] < 1000 else f"{model['delta_bic']:.1e}"
            aicc_str = f"{model['aicc']:.2f}" if model["aicc"] != float("inf") else "∞"

            result_text += (
                f"\n| {model['name'][:12]} | {model['loss_value']:.2e} | {model['k_effective']} | {model['sample_size']} | "
                f"{model['aic']:.2f} | {model['bic']:.2f} | {aicc_str} | {delta_aic_str} | {delta_bic_str} | {weight_str} |"
            )

        # Check if any models used independence assumption and add warning
        any_assumes_independence = any(m.get("assumes_independence", False) for m in valid_models)
        if any_assumes_independence:
            independence_models = [m["name"] for m in valid_models if m.get("assumes_independence", False)]
            result_text += f"""

⚠️  **Independence Assumption**: Sample sizes for the following models were inferred by counting
scalar values in output data: {", ".join(independence_models)}. This assumes each scalar is an
independent residual, which may be incorrect for multi-output, time series, spatial, or
hierarchical data. If residuals are correlated, effective sample sizes are smaller and
comparisons may be unreliable."""

        # Add parameter settings summary
        result_text += """

## Parameter Settings Applied to All Models
"""

        # Document the key parameter choices
        if df_effective is not None:
            result_text += f"- **Degrees of Freedom:** Using df_effective = {df_effective} (penalized/constrained models)\n"
        else:
            result_text += "- **Degrees of Freedom:** Using each model's k_params (standard MLE)\n"

        scale_status = "included" if include_scale_param else "excluded"
        result_text += f"- **Scale Parameter:** {scale_status} in AIC/BIC complexity penalty\n"

        aicc_scale_status = "included" if aicc_include_scale else "excluded"
        result_text += f"- **AICc Scale Parameter:** {aicc_scale_status} in small-sample correction\n"

        if n_obs is not None:
            result_text += f"- **Sample Size:** Explicit n_obs = {n_obs} used for all models\n"
        else:
            result_text += "- **Sample Size:** Inferred from each model's output data (independence assumed)\n"

        result_text += """

## Model Selection Recommendations

### AIC-based (Prediction Focus):
"""

        # AIC interpretation
        top_aic_models = [m for m in valid_models if m["delta_aic"] <= 2.0]
        if len(top_aic_models) == 1:
            result_text += f"- **Clear winner:** {top_aic_models[0]['name']} has substantial support (ΔAIC = 0)\n"
        else:
            result_text += f"- **{len(top_aic_models)} competitive models** (ΔAIC ≤ 2): {', '.join([m['name'] for m in top_aic_models])}\n"
            result_text += "- Consider model averaging or ensemble methods\n"

        # Evidence ratios
        worst_aic = max([m["delta_aic"] for m in valid_models])
        if worst_aic > 10:
            result_text += f"- **Strong evidence** against worst model (ΔAIC = {worst_aic:.1f})\n"

        result_text += """
### BIC-based (Parsimony Focus):
"""

        # BIC interpretation
        top_bic_models = [m for m in valid_models if m["delta_bic"] <= 2.0]
        if len(top_bic_models) == 1:
            result_text += f"- **Clear winner:** {top_bic_models[0]['name']} (ΔBIC = 0)\n"
        else:
            result_text += f"- **{len(top_bic_models)} competitive models** (ΔBIC ≤ 2): {', '.join([m['name'] for m in top_bic_models])}\n"

        # Sample size guidance - check if all models have same n
        sample_sizes = [m["sample_size"] for m in valid_models]
        if len(set(sample_sizes)) == 1:
            sample_size = sample_sizes[0]
            if sample_size < 40:
                result_text += f"\n### Sample Size Guidance (n = {sample_size}):\n"
                result_text += "- **Small sample**: Use AICc for model selection\n"
                result_text += "- BIC may be overly conservative\n"
            elif sample_size > 150:
                result_text += f"\n### Sample Size Guidance (n = {sample_size}):\n"
                result_text += "- **Large sample**: BIC provides consistent model selection\n"
                result_text += "- AIC may allow overfitting\n"
        else:
            result_text += "\n### Sample Size Guidance:\n"
            result_text += f"- **Mixed sample sizes**: {min(sample_sizes)} to {max(sample_sizes)}\n"
            result_text += "- Use per-model n for interpretation (shown in table above)\n"

        # Evidence ratio calculation
        if len(valid_models) >= 2 and valid_models[1]["akaike_weight"] > 0:
            er = valid_models[0]["akaike_weight"] / valid_models[1]["akaike_weight"]
            result_text += f"\n**Evidence ratio:** {er:.1f}x in favor of the best model\n"

        # Akaike weights interpretation
        result_text += """

## Akaike weights (relative likelihoods): weight for prediction focus
"""

        for model in valid_models[:3]:  # Top 3 models
            result_text += f"- **{model['name']}:** {model['akaike_weight']:.1%} relative likelihood of being best for prediction\n"

        if len(valid_models) > 3:
            others_weight = sum([m["akaike_weight"] for m in valid_models[3:]])
            result_text += f"- **Others:** {others_weight:.1%} combined relative likelihood\n"

        # Final recommendation
        result_text += """

## Final Recommendation:
"""

        if best_aic_model["name"] == best_bic_model["name"]:
            result_text += f"**{best_aic_model['name']}** - Consensus choice (best by both AIC and BIC)\n"
        else:
            result_text += f"**Split decision:** AIC favors {best_aic_model['name']}, BIC favors {best_bic_model['name']}\n"
            result_text += "Consider your priority: prediction accuracy (AIC) vs. model simplicity (BIC)\n"

        # Add failed models if any
        failed_models = [m for m in model_results if "error" in m]
        if failed_models:
            result_text += "\n## Failed Model Calculations:\n"
            for failed in failed_models:
                result_text += f"- **{failed['name']}:** {failed['error']}\n"

        return ToolResult(
            content=[TextContent(type="text", text=result_text)],
            structured_content={
                "valid_models": valid_models,
                "best_aic_model": best_aic_model["name"],
                "best_bic_model": best_bic_model["name"],
                "sample_size": sample_size,
                "failed_models": failed_models,
            },
        )

    except Exception as e:
        error_text = f"""❌ **Model Comparison Failed**

**Error:** {e!s}

## Required Model Format:
Each model must include:
- **name**: Model identifier (string)
- **loss_value**: Final loss from optimization (float ≥ 0)
- **cost_function_type**: Either 'mse' (Gaussian) or 'mae' (Laplace)
- **n_parameters**: Number of fitted parameters (int > 0)
## Example:
```python
models = [
    {{
        "name": "ExponentialModel",
        "loss_value": 0.01,
        "cost_function_type": "mse",
        "n_parameters": 3
    }},
    {{
        "name": "PolynomialModel",
        "loss_value": 0.02,
        "cost_function_type": "mse",
        "n_parameters": 4
    }}
]
data_file = "data.csv"
output_data = {{"columns": ["y"], "name": "y", "unit": "dimensionless"}}
```
"""
        return ToolResult(content=[TextContent(type="text", text=error_text)])


@mcp.tool(
    name="compute_parameter_covariance",
    description="""Compute parameter covariance matrices for fitted model parameters.

    Provides uncertainty estimates using robust Huber-White sandwich estimator and
    classical inverse Hessian approach. Use after fit_model to quantify parameter
    uncertainty and correlations.

    REQUIRED: Fitted parameters, model definition, same data used in fitting, variance estimate.
    RETURNS: Covariance matrices, standard errors, correlation matrix.
    """,
    tags=["statistics", "uncertainty", "covariance", "parameter_estimation"],
)
async def compute_parameter_covariance(
    model_name: Annotated[str, "Model name (e.g., 'ExponentialDecay', 'RingResonator')"],
    function_source: Annotated[str, "JAX function source code. MUST use jnp operations: jnp.exp, jnp.sin, etc."],
    function_name: Annotated[str, "Function name that computes the model output"],
    parameters: Annotated[list, "Fitted parameter values: [{'name': 'a', 'value': {'magnitude': 2.0, 'unit': 'dimensionless'}}]"],
    bounds: Annotated[
        list,
        "ALL parameter/input/output bounds: [{'name': 'a', 'lower': {'magnitude': 0, 'unit': 'dimensionless'}, 'upper': {'magnitude': 10, 'unit': 'dimensionless'}}]",  # noqa E501
    ],
    data_file: Annotated[str, "Path to data file (CSV, Excel, JSON, Parquet). All data must be provided via file."],
    input_data: Annotated[
        list, "Input column mappings: [{'column': 'time', 'name': 't', 'unit': 'second'}, {'column': 'x_col', 'name': 'x', 'unit': 'meter'}]"
    ],
    output_data: Annotated[
        dict, "Output column mapping: {'columns': ['signal'], 'name': 'y', 'unit': 'volt'} OR {'columns': ['y1', 'y2'], 'name': 'y', 'unit': 'volt'}"
    ],
    file_format: Annotated[str | None, "File format: 'csv', 'excel', 'json', 'parquet' (auto-detect if None)"] = None,
    variance: Annotated[
        float | str | None,
        "Noise variance (σ²) for uncertainty quantification. Estimate from residuals or domain knowledge. (estimated from loss if None)",
    ] = None,
    constants: Annotated[list | None, "Fixed constants: [{'name': 'c', 'value': {'magnitude': 3.0, 'unit': 'meter'}}]"] = None,
    docstring: Annotated[str, "Brief description of the model"] = "",
    cost_function_type: Annotated[str, "Cost function: 'mse' (default), 'mae'"] = "mse",
    jit_compile: Annotated[bool, "Enable JIT compilation for performance"] = True,
    scale_params: Annotated[bool, "Enable parameter scaling for numerical stability"] = False,
) -> ToolResult:
    """Compute parameter covariance matrix for fitted model parameters."""

    try:
        if data_file is None:
            raise ValueError("data_file is required. All data must be provided via file.")
        if input_data is None:
            raise ValueError("input_data is required when using file-based input.")
        if output_data is None:
            raise ValueError("output_data is required when using file-based input.")

        # Handle string-to-float conversion for variance (JSON might pass it as string)
        if variance is not None:
            try:
                variance = float(variance)
            except Exception as e:
                raise ValueError(f"variance must be a number. Error: {e!s}") from e

        resolved_input_data, resolved_output_data = resolve_data_input(
            data_file=data_file, input_data=input_data, output_data=output_data, file_format=file_format
        )

        input_names, const_names, param_names, bounds_names, n = validate_optimization_inputs(
            resolved_input_data, resolved_output_data, parameters, bounds, constants
        )

        prepare_bounds_for_optimization(bounds, input_names, const_names, resolved_output_data["name"])

        if variance is not None and variance <= 0:
            raise ValueError("variance must be positive (σ² > 0). Estimate it from residuals (e.g., final_loss for MSE) or domain knowledge.")

    except ValueError as e:
        return ToolResult(content=[TextContent(type="text", text=str(e))])

    if constants is None:
        constants = []

    request_data = {
        "model_name": model_name,
        "parameters": parameters,
        "bounds": bounds,
        "constants": constants,
        "input": resolved_input_data,
        "target": resolved_output_data,
        "function_source": function_source,
        "function_name": function_name,
        "docstring": docstring,
        "jit_compile": jit_compile,
        "cost_function_type": cost_function_type,
        "scale_params": scale_params,
        "variance": variance,
    }

    # Delegate to service
    service = CovarianceService()
    result = await service.compute_covariance(request_data)

    # Return formatted result
    if not result["success"]:
        return ToolResult(content=[TextContent(type="text", text=result["error"])])

    return ToolResult(
        content=[TextContent(type="text", text=result["markdown_report"])],
        structured_content={
            "parameters": result["parameters"],
            "sandwich_covariance": result["sandwich_covariance"],
            "inverse_hessian_covariance": result["inverse_hessian_covariance"],
            "sandwich_correlation": result["sandwich_correlation"],
            "inverse_hessian_correlation": result["inverse_hessian_correlation"],
            "parameter_names": result["parameter_names"],
            "sandwich_std_errors": result["sandwich_std_errors"],
            "inverse_hessian_std_errors": result["inverse_hessian_std_errors"],
        },
    )


def main():
    """Main entry point for the model fitting MCP server."""
    mcp.run()
