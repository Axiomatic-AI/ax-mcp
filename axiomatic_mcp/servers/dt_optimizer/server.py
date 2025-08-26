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
        "ALL parameter/input/output bounds: [{'name': 'a', 'lower': {'magnitude': 0, 'unit': 'dimensionless'}, 'upper': {'magnitude': 10, 'unit': 'dimensionless'}}]",  # noqa: E501
    ],
    input_data: Annotated[dict, "Input data: {'name': 'wavelength', 'unit': 'nanometer', 'magnitudes': [1550, 1551, ...]}"],
    target_data: Annotated[dict, "Target data: {'name': 'transmission', 'unit': 'dimensionless', 'magnitudes': [0.8, 0.6, ...]}"],
    # Optional parameters with defaults
    constants: Annotated[list | None, "Fixed constants: [{'name': 'c', 'value': {'magnitude': 3.0, 'unit': 'meter'}}]"] = None,
    docstring: Annotated[str, "Brief description of the model"] = "",
    tolerance: Annotated[float, "Optimization tolerance"] = 1e-6,
    optimizer_type: Annotated[str, "Optimizer: 'nlopt' (best default), 'scipy' (simple), 'nevergrad' (gradient-free)"] = "nlopt",
    cost_function_type: Annotated[str, "Cost function: 'mse' (default), 'mae', 'huber (with delta=1.0)', 'relative_mse'"] = "mse",
    max_time: Annotated[int, "Maximum optimization time in seconds"] = 5,
    jit_compile: Annotated[bool, "Enable JIT compilation for performance"] = True,
    optimizer_config: Annotated[dict | None, "Optimizer config: {'use_gradient': True, 'tol': 1e-6, 'max_function_eval': 1000000}"] = None,
) -> ToolResult:
    """Optimize a digital twin model using the Axiomatic AI platform."""

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


@mcp.prompt(
    name="optimization_workflow", description="Generic workflow for digital twin optimization - works with many different mathematical models"
)
def optimization_workflow() -> str:
    """Generate a generic optimization workflow guide."""

    return """# Digital Twin Optimization Workflow

## Step-by-Step Process:

### 1️⃣ **Define Your Mathematical Model**
Write your model as a JAX function:
```python
def target_variable_name(input_var, param1, param2, ...):
    # Analytical functions - use jnp.* operations
    return param1 * jnp.exp(-param2 * input_var) + param3
```

### 2️⃣ **Choose a Template**
Call `get_optimization_examples` to see available templates:
- **Analytical functions** (exponential, polynomial, trigonometric)
- **ODE systems** (population dynamics, chemical kinetics)

Pick the template closest to your model structure.

### 3️⃣ **Adapt the Template**
- Replace the function with your model
- Update parameter names and initial guesses
- Set realistic bounds for all parameters AND input/output variables
- Use proper pint units ('dimensionless', 'nanometer', 'volt', 'second', etc.)

### 4️⃣ **Ensure all Data is structured correctly following the Template**
```python
input_data = {"name": "time", "unit": "second", "magnitudes": [0, 1, 2, 3, ...]}
target_data = {"name": "concentration", "unit": "molar", "magnitudes": [1.0, 0.8, 0.6, ...]}
```

### 5️⃣ **Run Optimization**
Use `optimize_digital_twin_model` with your adapted template.

## Template Selection Guide:
1. **Simple analytical?** → Use polynomial/exponential templates
2. **Time-dependent dynamics?** → Use ODE templates
3. **Custom physics?** → Adapt the closest template structure

## Key Requirements:
- ALL functions must use JAX operations or JAX libraries (jnp.exp, jnp.sin, etc.)
- Every parameter needs bounds (reasonable ranges)
- Input AND output variables need bounds too

Ready to optimize? Get templates with `get_optimization_examples`!"""


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

    # Generic templates covering different model categories
    templates = {
        "analytical_exponential": {
            "category": "Analytical Function",
            "description": "Single exponential decay/growth with offset - good for radioactive decay, signal attenuation, population growth",
            "model_name": "ExponentialModel",
            "function_source": "def y(t, amplitude, decay_rate, offset):\n    return amplitude * jnp.exp(-decay_rate * t) + offset",
            "function_name": "y",
            "docstring": "Exponential model template",
            "parameters": [
                {"name": "amplitude", "value": {"magnitude": 2.0, "unit": "dimensionless"}},
                {"name": "decay_rate", "value": {"magnitude": 0.5, "unit": "dimensionless"}},
                {"name": "offset", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
            ],
            "bounds": [
                {"name": "amplitude", "lower": {"magnitude": 0.1, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
                {"name": "decay_rate", "lower": {"magnitude": 0.01, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
                {"name": "offset", "lower": {"magnitude": -5.0, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
                {"name": "t", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
                {"name": "y", "lower": {"magnitude": -1.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
            ],
            "input_data": {"name": "t", "unit": "dimensionless", "magnitudes": [0, 1, 2, 3, 4]},
            "target_data": {"name": "y", "unit": "dimensionless", "magnitudes": [2.0, 1.2, 0.8, 0.5, 0.4]},
            "optimizer_type": "nlopt",
            "cost_function_type": "mse",
            "max_time": 5,
            "tolerance": 1e-06,
            "jit_compile": True,
            "optimizer_config": {"use_gradient": True, "tol": 1e-06},
        },
        "analytical_polynomial": {
            "category": "Analytical Function",
            "description": "Polynomial function - good for parabolic relationships, response curves",
            "model_name": "PolynomialModel",
            "function_source": "def y(x, a, b, c):\n    return a * x**2 + b * x + c",
            "function_name": "y",
            "docstring": "Polynomial model template",
            "parameters": [
                {"name": "a", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
                {"name": "b", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
                {"name": "c", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
            ],
            "bounds": [
                {"name": "a", "lower": {"magnitude": -10.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
                {"name": "b", "lower": {"magnitude": -10.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
                {"name": "c", "lower": {"magnitude": -10.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
                {"name": "x", "lower": {"magnitude": -5.0, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
                {"name": "y", "lower": {"magnitude": -10.0, "unit": "dimensionless"}, "upper": {"magnitude": 50.0, "unit": "dimensionless"}},
            ],
            "input_data": {"name": "x", "unit": "dimensionless", "magnitudes": [-2, -1, 0, 1, 2]},
            "target_data": {"name": "y", "unit": "dimensionless", "magnitudes": [5, 2, 1, 2, 5]},
            "optimizer_type": "nlopt",
            "cost_function_type": "mse",
            "max_time": 5,
            "tolerance": 1e-06,
            "jit_compile": True,
            "optimizer_config": {"use_gradient": True, "tol": 1e-06},
        },
        "analytical_trigonometric": {
            "category": "Analytical Function",
            "description": "Sinusoidal oscillation - good for periodic signals, vibrations, waves",
            "model_name": "SinusoidalModel",
            "function_source": "def y(t, amplitude, frequency, phase, offset):\n    return amplitude * jnp.sin(2 * jnp.pi * frequency * t + phase) + offset",  # noqa: E501
            "function_name": "y",
            "docstring": "Sinusoidal model template",
            "parameters": [
                {"name": "amplitude", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
                {"name": "frequency", "value": {"magnitude": 0.5, "unit": "dimensionless"}},
                {"name": "phase", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
                {"name": "offset", "value": {"magnitude": 0.0, "unit": "dimensionless"}},
            ],
            "bounds": [
                {"name": "amplitude", "lower": {"magnitude": 0.1, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
                {"name": "frequency", "lower": {"magnitude": 0.1, "unit": "dimensionless"}, "upper": {"magnitude": 2.0, "unit": "dimensionless"}},
                {"name": "phase", "lower": {"magnitude": -3.14, "unit": "dimensionless"}, "upper": {"magnitude": 3.14, "unit": "dimensionless"}},
                {"name": "offset", "lower": {"magnitude": -2.0, "unit": "dimensionless"}, "upper": {"magnitude": 2.0, "unit": "dimensionless"}},
                {"name": "t", "lower": {"magnitude": 0.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
                {"name": "y", "lower": {"magnitude": -3.0, "unit": "dimensionless"}, "upper": {"magnitude": 3.0, "unit": "dimensionless"}},
            ],
            "input_data": {"name": "t", "unit": "dimensionless", "magnitudes": [0, 1, 2, 3, 4, 5]},
            "target_data": {"name": "y", "unit": "dimensionless", "magnitudes": [0, 1, 0, -1, 0, 1]},
            "optimizer_type": "nlopt",
            "cost_function_type": "mse",
            "max_time": 5,
            "tolerance": 1e-06,
            "jit_compile": True,
            "optimizer_config": {"use_gradient": True, "tol": 1e-06},
        },
    }

    # Concise template overview for LLMs
    template_summary = {}
    for key, template in templates.items():
        template_summary[key] = {
            "category": template["category"],
            "description": template["description"],
            "function": template["function_source"].split("\n")[0],  # Just the function signature
            "parameters": len(template["parameters"]),
            "use_cases": template["description"].split(" - ")[1] if " - " in template["description"] else "General modeling",
        }

    summary_text = f"""# 🧬 Digital Twin Optimization Templates

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
5. **Run optimization** with `optimize_digital_twin_model`

## Template Details:
{json.dumps(template_summary, indent=2)}

Use `optimization_workflow` prompt for detailed step-by-step guidance!
All templates are generic - adapt the function, parameters, and data to your specific model."""

    return ToolResult(
        content=[TextContent(type="text", text=summary_text)],
        structured_content={"templates": templates},
    )


def main():
    """Main entry point for the dt_optimizer MCP server."""
    mcp.run()
