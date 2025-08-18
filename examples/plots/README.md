# Plot Data Extraction Examples

This directory contains examples demonstrating how to extract numerical data from plot images using the axiomatic-plots MCP server.

## Structure

Each example directory contains:
- `plot.png` - The input plot image
- `prompt.md` - The extraction query
- `response.md` - The extracted data and analysis
- `plot_data.json` - Raw numerical data in JSON format

## Examples

- **example_0-4** - Various plot extraction scenarios
- **single_synthetic** - Single line plot with synthetic data
- **single_real** - Real-world single plot extraction
- **multi_synthetic** - Multi-series plot extraction

## Usage

The axiomatic-plots server can extract data points from line plots and scatter plots, converting visual information into structured numerical data for further analysis.