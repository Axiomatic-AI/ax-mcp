# Axiomatic Model Builder Server

An MCP server that provides physics model building capabilities using the Axiomatic AI platform. The server analyzes scientific literature and experimental data to automatically generate physics models with optimized parameters.

## Overview

The Model Builder server enables AI assistants to create physics models by combining insights from PDF documents (scientific papers, research reports) with experimental data from CSV files. It leverages advanced AI to understand the physical phenomena described in the literature and fits models to the provided data.

## Tools Available

### `build_model`

Builds a physics model using the Axiomatic AI Platform by analyzing a PDF document and fitting the model to data from a CSV file.

**Parameters:**

- `file_path` (Path, required): The absolute path to the PDF file to analyze for model insights
- `data_path` (Path, required): The absolute path to the CSV data file to fit the model against
- `query` (str, required): The specific instructions or query describing what kind of model to build

**Returns:**

- `ToolResult`: Structured response containing:
  - `physics_model_code`: Python code implementing the physics model
  - `parameters`: Dictionary of optimized model parameters with their fitted values
  - `optimization_results`: Detailed results from the parameter optimization process
  - `last_message`: Summary message from the model building process

**Features:**

- **Literature-Informed Modeling**: Extracts physical principles and equations from scientific papers
- **Data-Driven Optimization**: Automatically fits model parameters to experimental data
- **Python Code Generation**: Produces executable Python code for the physics model
- **Parameter Extraction**: Identifies and optimizes relevant physical parameters
- **File Output**: Automatically saves the generated model and parameters to files

**Example Usage:**

```
Build a physics model for heat transfer using the research paper at /papers/thermal_analysis.pdf and fit it to the experimental data in /data/temperature_measurements.csv
```

```
Create a mechanical vibration model based on the methodology in /docs/vibration_study.pdf using the sensor data from /experiments/accelerometer_data.csv
```

## Installation

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-model-builder&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4aW9tYXRpYy1tb2RlbC1idWlsZGVyIiwiZW52Ijp7IkFYSU9NQVRJQ19BUElfS0VZIjoiQVhJT01BVElDLUFQSS1LRVkifX0%3D)

### Quick Install (via PyPI)

Add to your MCP client configuration:

```json
{
  "axiomatic-model-builder": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-model-builder"],
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
  "axiomatic-model-builder": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.model_builder"],
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

- **Experimental Analysis**: Build physics models that explain experimental observations
- **Parameter Estimation**: Extract physical parameters from experimental data using theoretical frameworks
- **Model Validation**: Compare theoretical models from literature with experimental results
- **Hypothesis Testing**: Generate models based on theoretical papers and test against data

### Engineering Applications

- **System Modeling**: Create physics-based models for engineering systems from technical documentation
- **Performance Optimization**: Build models to optimize system parameters using experimental data
- **Design Validation**: Validate engineering designs by comparing theoretical models with test data

### Educational Applications

- **Model Demonstration**: Generate physics models that illustrate concepts from textbooks
- **Data Analysis**: Help students understand how theoretical models relate to experimental data
- **Research Projects**: Assist in building models for student research projects

## Output Files

The server automatically generates two files in the same directory as the input PDF:

1. **`physics_model.py`** (or uniquely named variant): Contains the complete Python implementation of the physics model
2. **`parameters.json`** (or uniquely named variant): Contains the optimized parameter values in JSON format

## Model Response Structure

The generated model includes:

- **Physics Model Code**: Complete Python implementation ready for execution
- **Parameters**: Dictionary of fitted parameter names and their optimized values
- **Optimization Results**: Detailed information about the fitting process, including convergence metrics
- **Last Message**: Human-readable summary of the model building process

## Best Practices

1. **Quality Inputs**: Use high-quality PDF documents with clear physics content and well-structured CSV data
2. **Descriptive Queries**: Provide specific, detailed queries about the type of model you want to build
3. **Data Format**: Ensure CSV data is properly formatted with clear column headers
4. **File Paths**: Use absolute file paths for reliable file access

## Limitations

- Currently supports PDF files for literature input only
- Requires CSV format for experimental data
- Model complexity depends on the quality of input documents and data
- Requires internet connection for API access
- File size limitations based on API constraints
- Processing time depends on document complexity and data size

## Support

For issues or questions:

- GitHub Issues: https://github.com/axiomatic/ax-mcp/issues
- Email: developers@axiomatic.ai

