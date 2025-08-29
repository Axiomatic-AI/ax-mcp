# Axiomatic Annotations Server

An MCP server that provides intelligent annotation capabilities for PDF documents using the Axiomatic AI platform's advanced document analysis and understanding models.

## Overview

The Annotations server enables AI assistants to create detailed, contextual annotations for PDF documents based on specific queries or instructions. It extracts relevant information, equations, parameters, and contextual descriptions to provide comprehensive analysis of document content.

## Tools Available

### `annotate_pdf`

Analyzes and annotates a PDF document with detailed contextual information based on user-specified instructions.

**Parameters:**

- `file_path` (Path, required): The absolute path to the PDF file to annotate
- `query` (str, required): The specific instructions or query to use for annotating the file

**Returns:**

- `AnnotationsResponse`: Structured annotations containing:
  - Multiple `PDFAnnotation` objects with detailed analysis
  - Page-specific location information
  - Contextual descriptions and explanations
  - Extracted equations in LaTeX format
  - Parameter values, names, and units
  - Categorization tags for organization

**Features:**

- **Smart Content Analysis**: Uses Google Gemini 2.5 Flash for document understanding
- **Equation Extraction**: Automatically identifies and formats equations in LaTeX
- **Parameter Detection**: Extracts parameter names, values, and units
- **Contextual Descriptions**: Provides meaningful explanations for each annotation
- **Precise Citations**: References exact page locations for all annotations

**Example Usage:**

```
Annotate the research paper at /path/to/paper.pdf focusing on methodology and key findings
```

```
Extract all equations and their parameters from the technical document at /documents/spec.pdf
```

## Installation

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-annotations&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4aW9tYXRpYy1hbm5vdGF0aW9ucyIsImVudiI6eyJBWElPTUFUSUNfQVBJX0tFWSI6IkFYSU9NQVRJQy1BUEktS0VZIn19)


### Quick Install (via PyPI)

Add to your MCP client configuration:

```json
{
  "axiomatic-annotations": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-annotations"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here",
    }
  }
}
```

### Development Install

For development or local modifications:

```json
{
  "axiomatic-annotations": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.annotations"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here",
    }
  }
}
```

## Configuration

### Required Environment Variables

- `AXIOMATIC_API_KEY`: Your Axiomatic AI API key (required)

See the [main README](../../../README.md#getting-an-api-key) for instructions on obtaining an API key.

## Use Cases

### Academic Research

- **Literature Review**: Extract key findings, methodologies, and conclusions from research papers
- **Equation Analysis**: Identify and catalog mathematical formulations across multiple papers
- **Parameter Extraction**: Build databases of experimental parameters and their values
- **Citation Support**: Generate detailed annotations with precise page references

### Technical Documentation

- **Specification Analysis**: Extract technical requirements and parameters from engineering documents
- **Compliance Review**: Identify critical sections and requirements in regulatory documents
- **Knowledge Extraction**: Convert complex technical content into structured annotations


### Educational Applications

- **Study Material Creation**: Generate comprehensive annotations for textbooks and papers
- **Concept Mapping**: Extract and organize key concepts with contextual explanations
- **Learning Support**: Create structured summaries of complex academic content

## Annotation Types

The server supports three primary annotation types:

1. **TEXT**: General textual content with contextual descriptions
2. **EQUATION**: Mathematical formulations in LaTeX format with parameter analysis
3. **FIGURE_DESCRIPTION**: Analysis and description of figures, charts, and diagrams

## Best Practices

1. **Specific Queries**: Provide clear, focused instructions for better annotation quality
2. **Document Quality**: Use high-quality PDF files for optimal text and equation recognition
3. **Query Refinement**: Iterate on queries to extract different aspects of the same document

## Limitations

- Currently supports PDF files only
- Requires internet connection for API access
- Processing time depends on document complexity and length
- File size limitations based on API constraints

## Support

For issues or questions:

- GitHub Issues: https://github.com/axiomatic/ax-mcp/issues
- Email: developers@axiomatic.ai

