"""Digital Twin Optimizer MCP server using the Axiomatic API.

This server provides tools for fitting custom mathematical models to experimental data
using the Axiomatic AI platform's digital twin optimization API. It includes comprehensive
guidance, examples, and validation to help LLMs use the API correctly.
"""

import json
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...shared import AxiomaticAPIClient

mcp = FastMCP(
    name="Axiomatic Digital Twin Optimizer",
    instructions="""This server provides digital twin optimization using the Axiomatic AI platform.

    CRITICAL REQUIREMENTS for all function calls:
    1. ALL functions must use JAX operations: jnp.exp, jnp.sin, jnp.cos, jnp.sqrt, etc.
    2. ALL units must be valid pint units: 'dimensionless', 'nanometer', 'volt', 'second', etc.
    3. ALL parameters, constants, inputs, and targets need bounds defined
    4. Bounds must include input variables AND target variables

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
)


@mcp.tool(
    name="optimize_digital_twin_model",
    description="""Optimize a custom JAX mathematical model against experimental data.

    This tool fits user-defined mathematical models to data using numerical optimization.
    It requires JAX functions, valid pint units, and parameter bounds.

    REQUIREMENTS:
    - Functions must use JAX: jnp.exp(-b*x), jnp.sin(w*t), etc.
    - Units must be valid pint: 'dimensionless', 'nanometer', 'volt', etc.
    - All parameters need bounds for optimization
    - Bounds must include constants, input, and output variables too

    RETURNS: Optimized parameters, fit quality metrics, and Python/JSON files
    """,
    tags=["optimization", "curve_fitting", "digital_twin", "jax"],
)
async def optimize_digital_twin_model(
    # Required parameters first
    model_name: Annotated[str, "Model name (e.g., 'ExponentialDecay', 'RingResonator')"],
    function_source: Annotated[str, "JAX function source code. MUST use jnp operations: jnp.exp, jnp.sin, etc."],
    function_name: Annotated[str, "Function name that computes the model output"],
    parameters: Annotated[list, "Initial parameter guesses: [{'name': 'a', 'value': {'magnitude': 2.0, 'unit': 'dimensionless'}}]"],
    bounds: Annotated[
        list,
        "ALL parameter/input/output bounds: [{'name': 'a', 'lower': {'magnitude': 0, 'unit': 'dimensionless'}, 'upper': {'magnitude': 10, 'unit': 'dimensionless'}}]",
    ],
    input_data: Annotated[dict, "Input data: {'name': 'wavelength', 'unit': 'nanometer', 'magnitudes': [1550, 1551, ...]}"],
    target_data: Annotated[dict, "Target data: {'name': 'transmission', 'unit': 'dimensionless', 'magnitudes': [0.8, 0.6, ...]}"],
    # Optional parameters with defaults
    constants: Annotated[list, "Fixed constants: [{'name': 'c', 'value': {'magnitude': 3.0, 'unit': 'meter'}}]"] = [],
    docstring: Annotated[str, "Brief description of the model"] = "",
    tolerance: Annotated[float, "Optimization tolerance"] = 1e-6,
    optimizer_type: Annotated[str, "Optimizer: 'nlopt' (best default), 'scipy' (simple), 'nevergrad' (gradient-free)"] = "nlopt",
    cost_function_type: Annotated[str, "Cost function: 'mse' (default), 'mae', 'huber', 'relative_mse'"] = "mse",
    max_time: Annotated[int, "Maximum optimization time in seconds"] = 5,
    jit_compile: Annotated[bool, "Enable JIT compilation for performance"] = True,
    optimizer_config: Annotated[dict, "Optimizer config: {'use_gradient': True, 'tol': 1e-6, 'max_function_eval': 1000000}"] = {},
) -> ToolResult:
    """Optimize a digital twin model using the Axiomatic AI platform."""

    # Build API request exactly matching the expected format
    request_data = {
        "model_name": model_name,
        "parameters": parameters,
        "bounds": bounds,
        "constants": constants,
        "input": input_data,
        "target": target_data,
        "function_source": function_source,
        "function_name": function_name,
        "docstring": docstring,
        "jit_compile": jit_compile,
        "tolerance": tolerance,
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
5. **Data Alignment:** Input and target data should have same length

## Need Help? Try the example tool:
Use `get_optimization_examples` to see working examples.
"""
        return ToolResult(content=[TextContent(type="text", text=error_details)])


@mcp.tool(
    name="get_optimization_examples",
    description="""Get working examples of digital twin optimization based on real usage.

    Returns complete examples with proper JAX functions, pint units, and parameter bounds.
    These are actual examples from successful optimizations.
    """,
    tags=["examples", "tutorial", "templates"],
)
async def get_optimization_examples() -> ToolResult:
    """Get clean JSON examples ready to use with optimize_digital_twin_model."""

    examples = {
        "exponential_decay": {
            "model_name": "ExponentialDecay",
            "function_source": "def y(t, a, k, offset):\n    return a * jnp.exp(-k * t) + offset\n",
            "function_name": "y",
            "docstring": "ExponentialDecay model - y output",
            "parameters": [
                {"name": "a", "value": {"magnitude": 2.0, "unit": "dimensionless"}},
                {"name": "k", "value": {"magnitude": 0.8, "unit": "dimensionless"}},
                {"name": "offset", "value": {"magnitude": -0.5, "unit": "dimensionless"}},
            ],
            "bounds": [
                {"name": "a", "lower": {"magnitude": 1.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
                {"name": "k", "lower": {"magnitude": 0.05, "unit": "dimensionless"}, "upper": {"magnitude": 1.0, "unit": "dimensionless"}},
                {"name": "offset", "lower": {"magnitude": -1.0, "unit": "dimensionless"}, "upper": {"magnitude": 3.0, "unit": "dimensionless"}},
                {"name": "t", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 8.0, "unit": "dimensionless"}},
                {"name": "y", "lower": {"magnitude": 0.8, "unit": "dimensionless"}, "upper": {"magnitude": 5.5, "unit": "dimensionless"}},
            ],
            "input_data": {
                "name": "t",
                "unit": "dimensionless",
                "magnitudes": [
                    0.0,
                    0.333,
                    0.667,
                    1.0,
                    1.333,
                    1.667,
                    2.0,
                    2.333,
                    2.667,
                    3.0,
                    3.333,
                    3.667,
                    4.0,
                    4.333,
                    4.667,
                    5.0,
                    5.333,
                    5.667,
                    6.0,
                    6.333,
                    6.667,
                    7.0,
                    7.333,
                    7.667,
                    8.0,
                ],
            },
            "target_data": {
                "name": "y",
                "unit": "dimensionless",
                "magnitudes": [
                    5.425,
                    5.156,
                    4.718,
                    4.044,
                    3.705,
                    3.361,
                    3.430,
                    2.992,
                    2.741,
                    2.588,
                    2.243,
                    2.146,
                    1.888,
                    1.923,
                    1.638,
                    1.652,
                    1.616,
                    1.402,
                    1.409,
                    1.127,
                    1.058,
                    1.134,
                    1.033,
                    0.860,
                    0.905,
                ],
            },
            "optimizer_type": "nlopt",
            "cost_function_type": "mse",
            "max_time": 5,
            "tolerance": 1e-06,
            "jit_compile": True,
            "optimizer_config": {"use_gradient": True, "tol": 1e-06},
        },
        "difference_exponentials": {
            "model_name": "DifferenceOfExponentials",
            "function_source": "def y(x, a, b, c, d):\n    return a * jnp.exp(-b * x) - c * jnp.exp(-d * x)\n",
            "function_name": "y",
            "docstring": "DifferenceOfExponentials model - y output",
            "parameters": [
                {"name": "a", "value": {"magnitude": 3.0, "unit": "dimensionless"}},
                {"name": "b", "value": {"magnitude": 2.5, "unit": "dimensionless"}},
                {"name": "c", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
                {"name": "d", "value": {"magnitude": 10.0, "unit": "dimensionless"}},
            ],
            "bounds": [
                {"name": "a", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
                {"name": "b", "lower": {"magnitude": 1.0, "unit": "dimensionless"}, "upper": {"magnitude": 100.0, "unit": "dimensionless"}},
                {"name": "c", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
                {"name": "d", "lower": {"magnitude": 1.0, "unit": "dimensionless"}, "upper": {"magnitude": 100.0, "unit": "dimensionless"}},
                {"name": "x", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 2.0, "unit": "dimensionless"}},
                {"name": "y", "lower": {"magnitude": -0.03, "unit": "dimensionless"}, "upper": {"magnitude": 0.5, "unit": "dimensionless"}},
            ],
            "input_data": {
                "name": "x",
                "unit": "dimensionless",
                "magnitudes": [
                    0.0,
                    0.069,
                    0.138,
                    0.207,
                    0.276,
                    0.345,
                    0.414,
                    0.483,
                    0.552,
                    0.621,
                    0.690,
                    0.759,
                    0.828,
                    0.897,
                    0.966,
                    1.034,
                    1.103,
                    1.172,
                    1.241,
                    1.310,
                    1.379,
                    1.448,
                    1.517,
                    1.586,
                    1.655,
                    1.724,
                    1.793,
                    1.862,
                    1.931,
                    2.0,
                ],
            },
            "target_data": {
                "name": "y",
                "unit": "dimensionless",
                "magnitudes": [
                    0.012,
                    0.451,
                    0.237,
                    0.122,
                    0.067,
                    0.027,
                    0.011,
                    0.016,
                    0.016,
                    0.005,
                    -0.020,
                    -0.005,
                    0.003,
                    -0.004,
                    0.015,
                    -0.003,
                    0.007,
                    -0.007,
                    -0.010,
                    -0.012,
                    0.001,
                    -0.019,
                    0.026,
                    -0.016,
                    -0.001,
                    0.004,
                    0.000,
                    -0.003,
                    -0.005,
                    -0.004,
                ],
            },
            "optimizer_type": "nlopt",
            "cost_function_type": "mse",
            "max_time": 5,
            "tolerance": 1e-06,
            "jit_compile": True,
            "optimizer_config": {"use_gradient": True, "tol": 1e-06},
        },
        "simple_quadratic": {
            "model_name": "SimpleQuadratic",
            "function_source": "def y(x, a, b, c):\n    return a * x**2 + b * x + c\n",
            "function_name": "y",
            "docstring": "SimpleQuadratic model - y output",
            "parameters": [
                {"name": "a", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
                {"name": "b", "value": {"magnitude": 2.0, "unit": "dimensionless"}},
                {"name": "c", "value": {"magnitude": -5.0, "unit": "dimensionless"}},
            ],
            "bounds": [
                {"name": "a", "lower": {"magnitude": 0.5, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
                {"name": "b", "lower": {"magnitude": -5.0, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
                {"name": "c", "lower": {"magnitude": -10.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
                {"name": "x", "lower": {"magnitude": -5.0, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
                {"name": "y", "lower": {"magnitude": 2.8, "unit": "dimensionless"}, "upper": {"magnitude": 72.0, "unit": "dimensionless"}},
            ],
            "input_data": {
                "name": "x",
                "unit": "dimensionless",
                "magnitudes": [
                    -5.0,
                    -4.66,
                    -4.31,
                    -3.97,
                    -3.62,
                    -3.28,
                    -2.93,
                    -2.59,
                    -2.24,
                    -1.90,
                    -1.55,
                    -1.21,
                    -0.86,
                    -0.52,
                    -0.17,
                    0.17,
                    0.52,
                    0.86,
                    1.21,
                    1.55,
                    1.90,
                    2.24,
                    2.59,
                    2.93,
                    3.28,
                    3.62,
                    3.97,
                    4.31,
                    4.66,
                    5.0,
                ],
            },
            "target_data": {
                "name": "y",
                "unit": "dimensionless",
                "magnitudes": [
                    71.63,
                    62.31,
                    54.43,
                    46.80,
                    40.55,
                    33.55,
                    28.24,
                    23.83,
                    18.88,
                    14.05,
                    10.71,
                    8.32,
                    5.06,
                    3.86,
                    3.53,
                    2.81,
                    4.02,
                    3.51,
                    4.67,
                    6.71,
                    9.72,
                    12.79,
                    17.73,
                    20.76,
                    25.92,
                    31.87,
                    37.50,
                    44.55,
                    51.79,
                    59.92,
                ],
            },
            "optimizer_type": "nlopt",
            "cost_function_type": "mse",
            "max_time": 5,
            "tolerance": 1e-06,
            "jit_compile": True,
            "optimizer_config": {"use_gradient": True, "tol": 1e-06},
        },
    }

    return ToolResult(
        content=[TextContent(type="text", text=f"Ready-to-use examples:\n{json.dumps(examples, indent=2)}")],
        structured_content={"examples": examples},
    )


def main():
    """Main entry point for the dt_optimizer MCP server."""
    mcp.run()
