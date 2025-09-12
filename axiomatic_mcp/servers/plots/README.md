# AxPlotToData Server

An MCP server for extracting numerical data from plot images using the Axiomatic AI platform's advanced computer vision capabilities.

## Overview

The AxPlotToData server enables AI assistants to analyze images of scientific plots and extract precise numerical data points. This tool converts visual representations of data back into structured numerical format, making it invaluable for data recovery, analysis, and validation tasks.

## Tools Available

### `extract_numerical_series`

Analyzes images of line and scatter plots to extract precise numerical data points from all series in the plot.

**Parameters:**

- `plot_path` (Path, required): The absolute path to the plot image file (PNG format)
- `max_number_points_per_series` (int, optional, default=100): Maximum points returned per series using random sampling if needed

**Returns:**

- `SeriesPointsData`: Structured data containing:
  - Multiple series identified in the plot
  - Numerical (x, y) coordinate pairs for each series
  - Series identifiers for multi-series plots

**Features:**

- Multi-series plot support
- Automatic axis scale detection
- High precision data extraction
- Handles logarithmic and linear scales
- Smart sampling for dense datasets
- Preserves data relationships and trends

**Example Usage:**

```

Extract data points from the plot at /path/to/experiment_results.png

```

[Short Demo Video (Claude Code)](https://youtu.be/6PFVK_couxs)

## Installation

### Getting an API Key

[![Static Badge](https://img.shields.io/badge/Get%20your%20API%20key-6EB700?style=flat)](https://docs.google.com/forms/d/e/1FAIpQLSfScbqRpgx3ZzkCmfVjKs8YogWDshOZW9p-LVXrWzIXjcHKrQ/viewform)

### Cursor Installation

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-plots&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4aW9tYXRpYy1wbG90cyIsImVudiI6eyJBWElPTUFUSUNfQVBJX0tFWSI6InlvdXItYXBpLWtleS1oZXJlIn19)

### Quick Install (via PyPI)

Add to your MCP client configuration:

```json
{
  "axiomatic-plots": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-plots"],
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
  "axiomatic-plots": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.plots"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

## Configuration

### Required Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)

See the [main README](https://github.com/Axiomatic-AI/ax-mcp#getting-an-api-key) for instructions on obtaining an API key.

## Use Cases

### Scientific Research

- **Literature Data Extraction**: Recover data from published paper figures
- **Historical Data Recovery**: Digitize data from old plots and charts
- **Data Validation**: Compare extracted data with expected values
- **Meta-Analysis**: Combine data from multiple sources

### Engineering Applications

- **Performance Analysis**: Extract performance curves from datasheets
- **Calibration Data**: Digitize calibration curves from equipment manuals
- **Quality Control**: Compare measured vs. reference plots

### Data Processing

- **Format Conversion**: Convert visual data to CSV/JSON formats
- **Data Integration**: Merge plot data with existing datasets
- **Trend Analysis**: Extract trends from multiple plot sources
- **Benchmarking**: Compare results across different studies

## Limitations

- Currently supports PNG format only
- Best results with clear, high-resolution images
- Complex 3D plots not yet supported
- Heatmaps and contour plots require special handling
- Maximum practical limit on number of extracted points

## Best Practices

1. **Image Quality**: Use high-resolution, clear images
2. **Plot Clarity**: Ensure good contrast between data and background
3. **File Format**: Save plots as PNG for best results
4. **Series Separation**: Distinct colors/styles for multiple series
5. **Axis Labels**: Clear axis markings improve accuracy

## Integration Examples

A number of demos for the plots mcp can be found [here](https://github.com/Axiomatic-AI/ax-mcp/blob/main/examples/plots/README.md).

### Python Integration

```python
# After extracting data with MCP
import pandas as pd

# Convert extracted data to DataFrame
df = pd.DataFrame(points)
df.to_csv('extracted_data.csv')
```

### Data Analysis Workflow

1. Extract data from plot images
2. Export to preferred format (CSV, JSON)
3. Import into analysis tools (Python, R, MATLAB)
4. Perform statistical analysis or modeling

## Support

For issues or questions:

- GitHub Issues: https://github.com/axiomatic/ax-mcp/issues
- Email: developers@axiomatic.ai
