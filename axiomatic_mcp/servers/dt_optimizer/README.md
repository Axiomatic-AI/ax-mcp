# Axiomatic Digital Twin Optimizer Server

An MCP server for optimizing digital twin models using the Axiomatic AI platform's optimization algorithms and mathematical modeling capabilities.

## Overview

The Digital Twin Optimizer server enables AI assistants to optimize mathematical models against experimental or simulation data. It leverages multiple optimization algorithms (gradient-based, global search, and hybrid approaches) to find the best-fit parameters for complex systems including analytical functions, differential equations, and multi-component models.

## Tools Available

### `optimize_digital_twin_model`

Optimizes model parameters to fit experimental data using various optimization algorithms and cost functions.

**Parameters:**

- `function_source` (str, required): Python function definition using JAX operations (jnp.*)
- `parameters` (list, required): List of parameter specifications with name, initial value, and bounds
- `data_points` (list, required): List of data points with x, y values and optional units
- `optimizer_type` (str, optional, default="nlopt"): Optimization algorithm ("nlopt", "scipy", "nevergrad")
- `cost_function_type` (str, optional, default="mse"): Cost function ("mse", "mae", "huber", "relative_mse")
- `max_iterations` (int, optional, default=1000): Maximum optimization iterations
**Returns:**

- Optimized parameter values
- Optimization statistics (cost, iterations, convergence status)

**Features:**

- Multiple optimization algorithms:
  - **nlopt**: (Combination of global and local) gradient-based optimization
  - **scipy**: Uses scipy's `curve_fit` routine
  - **nevergrad**: Global optimization for complex landscapes
- Unit-aware optimization with automatic conversions
- Advanced cost functions including cost functions that are robust wrt outliers.
- Support for complex mathematical models using JAX

### `get_optimization_examples`

Provides template examples for common optimization scenarios to guide model development.

**Returns:**

- Comprehensive templates covering:
  - **Analytical Functions**: Exponential decay, polynomial fitting, trigonometric models
  - **Dynamic Systems**:
  - **Physical Models**:
- Complete parameter specifications and data formats
- Best practice recommendations for each model type

### `optimization_workflow`

Provides step-by-step guidance for setting up and executing optimization workflows.

**Returns:**

- Structured workflow covering:
  1. Model formulation and JAX implementation
  2. Parameter bounds and initial value selection
  3. Data preparation and unit consistency
  4. Optimizer and cost function selection
  5. Results interpretation and validation

**Example Usage:**

```
Optimize an exponential decay model with parameters amplitude, decay_rate, and offset using this experimental data: [(0, 10.2), (1, 7.8), (2, 5.9), (3, 4.2), (4, 3.1)]
```

(wait for response)
```


```
## Installation

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-dt-optimizer&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4aW9tYXRpYy1kdC1vcHRpbWl6ZXIiLCJlbnYiOnsiQVhJT01BVElDX0FQSV9LRVkiOiJFTlRFUiBZT1VSIEFQSSBLRVkifX0%3D)

### Quick Install (via PyPI)

Add to your MCP client configuration:

```json
{
  "axiomatic-dt-optimizer": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-dt-optimizer"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

### Development Install

For development or local modifications:

```json
{
  "axiomatic-dt-optimizer": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.dt_optimizer"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

## Configuration

### Required Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)

See the [main README](../../../README.md#getting-an-api-key) for instructions on obtaining an API key.

## Use Cases

### Scientific Research

- **Experimental Data Fitting**: Fit theoretical models to experimental measurements
- **Parameter Estimation**: Extract physical parameters from noisy data
- **Model Validation**: Compare different model formulations

### Engineering Applications

- **System Identification**: Identify dynamic system parameters from input-output data
- **Calibration**: Optimize sensor calibration models

### Data Analysis

- **Curve Fitting**: Fit analytical functions to measured data
- **Trend Analysis**: Model time-series data with physical insights
- **Multi-variate Optimization**: Handle complex parameter spaces
- **Robust Fitting**: Handle outliers with robust cost functions

## Example Model Types

### Analytical Functions
- **Exponential Models**: `amplitude * jnp.exp(-decay_rate * t) + offset`
- **Polynomial Models**: `a * x**2 + b * x + c`
- **Trigonometric Models**: `amplitude * jnp.sin(frequency * t + phase) + offset`
- **Power Laws**: `amplitude * jnp.power(x, exponent)`

### Dynamic Systems
- **First-Order ODEs**: Exponential approach to steady state
- **Multi-Component Systems**: Sum of exponentials with different time constants
- **Damped Oscillators**: Combined exponential and sinusoidal behavior

### Physical Units
- **Dimensionless**: Pure numbers without units
- **Time Units**: seconds, milliseconds, microseconds, etc.
- **Length Units**: meter, centimeter, millimeter, micrometer, nanometer, etc.
- **Frequency Units**: Hz, kHz, MHz, GHz, etc.

## Optimization Algorithms

### NLopt (Default)
- **Strengths**: Global search, gradient-based optimization
- **Best For**: General-purpose optimization
- **Features**: Multiple algorithm variants, constraint support

### SciPy
- **Strengths**: Robust, well-tested scientific algorithms
- **Best For**: General-purpose optimization, educational use
- **Features**: Fast, extensive documentation

### Nevergrad
- **Strengths**: Global optimization, handles complex landscapes
- **Best For**: Exploration-heavy problems
- **Features**: Population-based methods, noise tolerance

## Cost Functions

- **MSE (Mean Squared Error)**: Standard least-squares fitting
- **MAE (Mean Absolute Error)**: Robust to outliers
- **Huber**: Balanced between MSE and MAE
- **Relative MSE**: Scale-invariant for different data ranges

## Best Practices

1. **Model Formulation**: Use JAX operations (jnp.*) for all mathematical functions
2. **Parameter Bounds**: Set realistic bounds based on physical constraints
3. **Initial Values**: Choose initial parameters close to expected values

## Limitations

- Function source must use JAX operations for automatic differentiation
- Unit conversions limited to physical quantities available in [Pint](https://pint.readthedocs.io/en/stable/)
- Requires internet connection for API access

## Support

For issues or questions:

For issues or questions:

- GitHub Issues: [Axiomatic MCP Issues](https://github.com/Axiomatic-AI/ax-mcp/issues)
- Email: [developers@axiomatic-ai.com](mailto:developers@axiomatic-ai.com)
## Related Resources

- [JAX Documentation](https://jax.readthedocs.io/)
- [Pint Documentation](https://pint.readthedocs.io/en/stable/)
