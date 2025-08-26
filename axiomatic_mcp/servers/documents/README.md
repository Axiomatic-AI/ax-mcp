# Axiomatic Documents Server

An MCP server that provides document processing capabilities using the Axiomatic AI platform, with a focus on converting PDF documents to markdown format using advanced OCR technology.

## Overview

The Documents server enables AI assistants to read and process PDF documents from the filesystem, converting them into structured markdown format. This is particularly useful for extracting content from complex PDFs including those with tables, figures, and mathematical equations.

## Tools Available

### `document_to_markdown`

Converts a PDF document to markdown using Axiomatic's advanced OCR technology.

**Parameters:**

- `file_path` (Path, required): The absolute path to the PDF file to analyze

**Returns:**

- Markdown formatted text extracted from the PDF
- Suggested file creation with the converted markdown content

**Features:**

- Uses Mistral model for document understanding
- Employs DocLayout YOLO for layout analysis
- Preserves document structure including headings, lists, and tables
- Handles complex formatting and mathematical notation

**Example Usage:**

```
Use Axiomatic to convert the document I am looking at to Markdown
```

(wait for response)

```
Write the markdown to a file
```

## Installation

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-documents&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4aW9tYXRpYy1kb2N1bWVudHMiLCJlbnYiOnsiQVhJT01BVElDX0FQSV9LRVkiOiJFTlRFUiBZT1VSIEFQSSBLRVkifX0%3D)

### Quick Install (via PyPI)

Add to your MCP client configuration:

```json
{
  "axiomatic-documents": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-documents"],
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
  "axiomatic-documents": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.documents"],
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

- **Research Paper Analysis**: Convert academic PDFs to markdown for easier processing
- **Documentation Migration**: Transform PDF documentation into markdown for version control
- **Content Extraction**: Extract structured data from reports and forms
- **Accessibility**: Make PDF content accessible for text-based analysis

## Limitations

- Currently supports PDF files only
- Requires internet connection for API access
- File size limitations based on API constraints
- Processing time depends on document complexity

## Support

For issues or questions:

- GitHub Issues: https://github.com/axiomatic/ax-mcp/issues
- Email: developers@axiomatic.ai
