# AxModelFitter

An MCP server for fitting mathematical models to experimental data using the Axiomatic AI platform's optimization algorithms.

AxModelFitter enables AI assistants to fit mathematical models against experimental or simulation data using various optimization algorithms. The tools provided also enable the AI assistants to perform statistical analyses to assess fit quality, to ensure the data is neither over- nor underfit, and to select the best among multiple competing models.

## Model Fitting Tools

### `fit_model`

Fits mathematical models to experimental data using various optimization algorithms and cost functions.

**Arguments:**

- `model_name`: Model name (e.g., 'ExponentialDecay', 'RingResonator')
- `function_source`: JAX-compatible function source code
- `function_name`: Function name (e.g., 'y')
- `parameters`: Initial parameter guesses
- `bounds`:  ALL parameter/input/output bounds
- `data_file`: Path to your data file (CSV, Excel, JSON, Parquet)
- `input_data`: List mapping file columns to input variables  
- `output_data`: Dictionary mapping file columns to output variables

**Selected optional arguments**

- `max_time` (int): Maximum runtime in seconds (default: 5)
- `optimizer_type` (str): Optimization backend; one of {"nlopt", "scipy", "nevergrad"} (default: "nlopt")
- `cost_function_type` (str): Cost function; one of {"mse", "mae", "huber", "relative_mse"} (default: "mse")

**Returns:**

- Optimized parameter values
- Optimization statistics (cost, iterations, convergence status)

### `get_fitting_examples`

Provides template examples for common model fitting scenarios to guide development.

**Returns:**

- Comprehensive templates covering:
  - **Analytical Functions**
  - **Dynamic Systems**

### `get_workflow_prompt`

Provides step-by-step guidance for setting up and executing model fitting workflows.

**Returns:**

- Structured workflow covering:
  1. Model formulation and JAX implementation
  2. Parameter bounds and initial value selection
  3. File-based data loading and unit consistency checking
  4. Optimizer and cost function selection

### Statistical Analysis Tools

- **`calculate_r_squared`** - Calculate R² (coefficient of determination) for evaluating quality of model fit. 
- **`cross_validate_model`** - Perform cross-validation to assess model generalization capabilities and ensure data is neither over nor underfit.  
- **`calculate_information_criteria`** - Compute Akaike and Bayesian information criteria (AIC/BIC) for model comparison
- **`compare_models`** - Statistical comparison of multiple models based on AIC/BIC

**Example Usage:**

Via an LLM client such as Claude Desktop:

> Given this data x = [-5, -4.66, -4.31, -3.97, -3.62, -3.28, -2.93, -2.59, -2.24, -1.9, -1.55, -1.21, -0.86, -0.52, -0.17, 0.17, 0.52, 0.86, 1.21, 1.55, 1.9, 2.24, 2.59, 2.93, 3.28, 3.62, 3.97, 4.31, 4.66, 5], y = [71.63, 62.31, 54.43, 46.8, 40.55, 33.55, 28.24, 23.83, 18.88, 14.05, 10.71, 8.32, 5.06, 3.86, 3.53, 2.81, 4.02, 3.51, 4.67, 6.71, 9.72, 12.79, 17.73, 20.76, 25.92, 31.87, 37.5, 44.55, 51.79, 59.92], use the axiomatic tool to fit a parabola.

Example input for testing with the MCP Inspector (using file-based data):

**First, create a CSV file** (e.g., `quadratic_data.csv`):
```csv
x,y
-5,71.63
-4.66,62.31
-4.31,54.43
-3.97,46.8
-3.62,40.55
-3.28,33.55
-2.93,28.24
-2.59,23.83
-2.24,18.88
-1.9,14.05
-1.55,10.71
-1.21,8.32
-0.86,5.06
-0.52,3.86
-0.17,3.53
0.17,2.81
0.52,4.02
0.86,3.51
1.21,4.67
1.55,6.71
1.9,9.72
2.24,12.79
2.59,17.73
2.93,20.76
3.28,25.92
3.62,31.87
3.97,37.5
4.31,44.55
4.66,51.79
5,59.92
```

**Then use the `fit_model` tool**:
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
  "data_file": "/path/to/quadratic_data.csv",
  "input_data": [
    {"column": "x", "name": "x", "unit": "dimensionless"}
  ],
  "output_data": {
    "columns": ["y"], 
    "name": "y", 
    "unit": "dimensionless"
  },
  "optimizer_type": "nlopt",
  "cost_function_type": "mse",
  "max_time": 10
}
```

## Data Requirements

### File-Based Data Input
All tools require tabular data to be provided via files. Ideally the column names indicate the units of the quantities. Otherwise, the units must be made explicitly clear in the user prompt. 

Supported formats:

- **CSV** (`.csv`) - Most common, easy to create
- **Excel** (`.xlsx`, `.xls`) - Spreadsheet format
- **JSON** (`.json`) - Structured data format  
- **Parquet** (`.parquet`) - Efficient columnar format


**Examples:**
- Single input: `[{"column": "time", "name": "t", "unit": "second"}]`
- Single output: `{"columns": ["voltage"], "name": "v", "unit": "volt"}`
- Multi-output: `{"columns": ["x", "y"], "name": "position", "unit": "meter"}`

## Installation

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](cursor://anysphere.cursor-deeplink/mcp/install?name=AxModelFitter&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4bW9kZWxmaXR0ZXIiLCJlbnYiOnsiQVhJT01BVElDX0FQSV9LRVkiOiJ5b3VyLWFwaS1rZXktaGVyZSJ9fQ%3D%3D)

### Quick Install (via PyPI)

Add to your MCP client configuration:

```json
{
  "AxModelFitter": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axmodelfitter"],
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
  "AxModelFitter": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.axmodelfitter"],
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
2. **Data Preparation**: Create clean CSV/Excel files with clear column names
3. **Parameter Bounds**: Set realistic bounds based on physical constraints  
4. **Initial Values**: Choose initial parameters close to expected values
5. **File Formats**: Use CSV for simplicity, Parquet for large datasets

## Limitations

- Function source must use JAX-compatible operations for automatic differentiation
- Unit conversions limited to physical quantities available in [Pint](https://pint.readthedocs.io/en/stable/)
- **All data must be provided via files** - direct data input is no longer supported
- File columns must be numeric (non-numeric columns will cause errors)

## Support

For issues or questions:

- GitHub Issues: [Axiomatic MCP Issues](https://github.com/Axiomatic-AI/ax-mcp/issues)
- Email: [developers@axiomatic-ai.com](mailto:developers@axiomatic-ai.com)

## Related Resources

- [JAX Documentation](https://jax.readthedocs.io/)
- [Pint Documentation](https://pint.readthedocs.io/en/stable/)
