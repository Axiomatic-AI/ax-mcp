# Axiomatic Digital Twin Optimizer Server

An MCP server for optimizing digital twin models using the Axiomatic AI platform's optimization algorithms and mathematical modeling capabilities.

The Digital Twin Optimizer server enables AI assistants to optimize mathematical models against experimental or simulation data.

## Tools Available

### `optimize_digital_twin_model`

Optimizes model parameters to fit experimental data using various optimization algorithms and cost functions.

**Arguments:**

- `model_name`: Model name (e.g., 'ExponentialDecay', 'RingResonator')
- `function_source`: JAX-compatible function source code
- `function_name`: Function name (e.g., 'y')
- `parameters`: Initial parameter guesses
- `bounds`:  ALL parameter/input/output bounds
- `input_data` Input data
- `output_data` Output data

**Selected optional arguments**

- `max_time` (int): Maximum runtime in seconds (default: 5)
- `optimizer_type` (str): Optimization backend; one of {"nlopt", "scipy", "nevergrad"} (default: "nlopt")
- `cost_function_type` (str): Cost function; one of {"mse", "mae", "huber", "relative_mse"} (default: "mse")

**Returns:**

- Optimized parameter values
- Optimization statistics (cost, iterations, convergence status)

### `get_optimization_examples`

Provides template examples for common optimization scenarios to guide model development.

**Returns:**

- Comprehensive templates covering:
  - **Analytical Functions**
  - **Dynamic Systems**

### `optimization_workflow`

Provides step-by-step guidance for setting up and executing optimization workflows.

**Returns:**

- Structured workflow covering:
  1. Model formulation and JAX implementation
  2. Parameter bounds and initial value selection
  3. Data preparation and unit consistency
  4. Optimizer and cost function selection

**Example Usage:**

Via an LLM client such as Claude Desktop:

> Given this data x = [-5, -4.66, -4.31, -3.97, -3.62, -3.28, -2.93, -2.59, -2.24, -1.9, -1.55, -1.21, -0.86, -0.52, -0.17, 0.17, 0.52, 0.86, 1.21, 1.55, 1.9, 2.24, 2.59, 2.93, 3.28, 3.62, 3.97, 4.31, 4.66, 5], y = [71.63, 62.31, 54.43, 46.8, 40.55, 33.55, 28.24, 23.83, 18.88, 14.05, 10.71, 8.32, 5.06, 3.86, 3.53, 2.81, 4.02, 3.51, 4.67, 6.71, 9.72, 12.79, 17.73, 20.76, 25.92, 31.87, 37.5, 44.55, 51.79, 59.92], use the axiomatic tool to fit a parabola.

Example input for testing with the MCP Inspector
```json
{
  "model_name": "SimpleQuadratic",
  "function_source": "def y(x, a, b, c): return a * x**2 + b * x + c",
  "function_name": "y",
  "parameters": [
    {"name": "a", "value": {"magnitude": 1.0, "unit": "dimensionless"}},
    {"name": "b", "value": {"magnitude": 2.0, "unit": "dimensionless"}},
    {"name": "c", "value": {"magnitude": -5.0, "unit": "dimensionless"}}
  ],
  "bounds": [
    {"name": "a", "lower": {"magnitude": 0.5, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
    {"name": "b", "lower": {"magnitude": -5.0, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
    {"name": "c", "lower": {"magnitude": -10.0, "unit": "dimensionless"}, "upper": {"magnitude": 10.0, "unit": "dimensionless"}},
    {"name": "x", "lower": {"magnitude": -5.0, "unit": "dimensionless"}, "upper": {"magnitude": 5.0, "unit": "dimensionless"}},
    {"name": "y", "lower": {"magnitude": 2.8, "unit": "dimensionless"}, "upper": {"magnitude": 72.0, "unit": "dimensionless"}}
  ],
  "input_data": {
    "name": "x",
    "unit": "dimensionless",
    "magnitudes": [-5, -4.66, -4.31, -3.97, -3.62, -3.28, -2.93, -2.59, -2.24, -1.9, -1.55, -1.21, -0.86, -0.52, -0.17, 0.17, 0.52, 0.86, 1.21, 1.55, 1.9, 2.24, 2.59, 2.93, 3.28, 3.62, 3.97, 4.31, 4.66, 5]
  },
  "target_data": {
    "name": "y",
    "unit": "dimensionless",
    "magnitudes": [71.63, 62.31, 54.43, 46.8, 40.55, 33.55, 28.24, 23.83, 18.88, 14.05, 10.71, 8.32, 5.06, 3.86, 3.53, 2.81, 4.02, 3.51, 4.67, 6.71, 9.72, 12.79, 17.73, 20.76, 25.92, 31.87, 37.5, 44.55, 51.79, 59.92]
  },
  "optimizer_type": "nlopt",
  "cost_function_type": "mse",
  "max_time": 10
}
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

## Optimization Algorithms

- **NLopt (Default)**:  Global search, gradient-based and gradient-free optimization, constraint support
- **SciPy**: Fast local search. easy tasks
- **Nevergrad**: Global optimization, gradient-free

## Cost Functions

- **MSE (Mean Squared Error)**: Standard least-squares fitting
- **MAE (Mean Absolute Error)**: Robust to outliers
- **Huber**: Balanced between MSE and MAE with delta = 1.0.
- **Relative MSE**: Scale-invariant for different data ranges

## Best Practices

1. **Model Formulation**: Use JAX operations (jnp.*) for all mathematical functions
2. **Parameter Bounds**: Set realistic bounds based on physical constraints
3. **Initial Values**: Choose initial parameters close to expected values

## Limitations

- Function source must use JAX-compatible operations for automatic differentiation
- Unit conversions limited to physical quantities available in [Pint](https://pint.readthedocs.io/en/stable/)

## Support

For issues or questions:

- GitHub Issues: [Axiomatic MCP Issues](https://github.com/Axiomatic-AI/ax-mcp/issues)
- Email: [developers@axiomatic-ai.com](mailto:developers@axiomatic-ai.com)

## Related Resources

- [JAX Documentation](https://jax.readthedocs.io/)
- [Pint Documentation](https://pint.readthedocs.io/en/stable/)
