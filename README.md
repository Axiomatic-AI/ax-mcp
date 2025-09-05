# Axiomatic MCP Servers

MCP (Model Context Protocol) servers that provide AI assistants with access to the Axiomatic_AI Platform - a suite of advanced tools for scientific computing, document processing, and photonic circuit design.

## Available Servers

### 🖌️ [AxEquationExplorer](./axiomatic_mcp/servers/equations/)

Compose equation of your interest based on information in the scientific paper.

### 📄 [AxDocumentParser](./axiomatic_mcp/servers/documents/)

Convert PDF documents to markdown with advanced OCR and layout understanding.

### 📝 [AxDocumentAnnotator](./axiomatic_mcp/servers/annotations/)

Create intelligent annotations for PDF documents with contextual analysis, equation extraction, and parameter identification.

### ⚙️ [AxModelFitter](./axiomatic_mcp/servers/model_fitting/)

Fit parametric models or digital twins to observational data using advanced statistical analysis and optimization algorithms.

### 🔬 [AxPhotonicsPreview](./axiomatic_mcp/servers/pic/)

Design photonic integrated circuits using natural language descriptions.

### 📊 [AxPlotToData](./axiomatic_mcp/servers/plots/)

Extract numerical data from plot images for analysis and reproduction.

## Getting an API Key

All Axiomatic MCP servers require an API key:

1. Fill the following [form](https://docs.google.com/forms/d/e/1FAIpQLSfScbqRpgx3ZzkCmfVjKs8YogWDshOZW9p-LVXrWzIXjcHKrQ/viewform?usp=dialog) to request an Axiomatic_AI API key.
2. Add the API key to your MCP client configuration as `AXIOMATIC_API_KEY`

## Installation

### System requirements

- Python
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

### Individual MCP server installation

Installation instructions can be found for each specific server in their README.

### Install all servers

Copy the content of the [mcp-example.json](mcp-example.json) file into your AI client MCP server config json.

### Setting up MCP Servers in AI Clients

#### Claude Desktop

1. Open Claude Desktop settings
2. Navigate to Developer → Edit MCP config
3. Add the server configuration(s) above
4. Restart Claude Desktop

#### Cursor

1. Open Cursor settings (Cmd/Ctrl + ,)
2. Search for "MCP"
3. Add the server configuration(s) to the MCP settings
4. Restart Cursor

#### Other MCP Clients

Refer to your client's documentation for MCP server configuration.

## Troubleshooting

### Server not appearing in Cursor

1. Restart Cursor after updating MCP settings
2. Check the Output panel (View → Output → MCP) for errors
3. Verify the command path is correct

### Multiple servers overwhelming the LLM

Install only the domain servers you need. Each server runs independently, so you can add/remove them as needed.

### API connection errors

1. Verify your API key is set correctly
2. Check internet connection

## Support

- **Issues**: [GitHub Issues](https://github.com/axiomatic/ax-mcp/issues)
- **Email**: developers@axiomatic-ai.com
