# AxDocumentAnnotator Server

An MCP server that provides intelligent annotation capabilities for various document types using the Axiomatic AI platform's advanced document analysis and understanding models.

## Overview

The AxDocumentAnnotator server enables AI assistants to create detailed, contextual annotations for various file types (PDF, PNG, JPEG, Markdown, and text files) based on specific queries or instructions. It extracts relevant information, equations, parameters, and contextual descriptions to provide comprehensive analysis of document content.

## Tools Available

### `annotate_file`

Analyzes and annotates various file types with detailed contextual information based on user-specified instructions. Supports PDF, PNG, JPEG, Markdown, and text files.

**Parameters:**

- `file_path` (Path, required): The absolute path to the file to annotate
- `query` (str, required): The specific instructions or query to use for annotating the file

**Returns:**

- `AnnotationsResponse`: Structured annotations containing:
  - Multiple `Annotation` objects with detailed analysis (PDFAnnotation for PDF files with page numbers)
  - Page-specific location information (for PDF files)
  - Contextual descriptions and explanations
  - Extracted equations in LaTeX format
  - Parameter values, names, and units
  - Categorization tags for organization

**Features:**

- **Multi-Format Support**: Works with PDF, PNG, JPEG, Markdown, and text files
- **Smart Content Analysis**: Uses SOTA LLM for document understanding
- **Equation Extraction**: Automatically identifies and formats equations in LaTeX
- **Parameter Detection**: Extracts parameter names, values, and units
- **Contextual Descriptions**: Provides meaningful explanations for each annotation
- **Precise Citations**: References exact page locations for PDF files and appropriate locations for other formats

**Example Usage:**

```
Annotate the research paper at /path/to/paper.pdf focusing on methodology and key findings
```

```
Extract all equations and their parameters from the technical document at /documents/spec.pdf
```

```
Analyze the image at /images/diagram.png and describe the key components
```

```
Extract key concepts from the markdown file at /docs/guide.md
```

## Installation

### Getting an API Key

[![Static Badge](https://img.shields.io/badge/Get%20your%20API%20key-6EB700?style=flat)](https://docs.google.com/forms/d/e/1FAIpQLSfScbqRpgx3ZzkCmfVjKs8YogWDshOZW9p-LVXrWzIXjcHKrQ/viewform)

### Cursor Installation

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-annotations&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGF4aW9tYXRpYy1hbm5vdGF0aW9ucyIsImVudiI6eyJBWElPTUFUSUNfQVBJX0tFWSI6IkFYSU9NQVRJQy1BUEktS0VZIn19)

### Quick Install (via PyPI)

Add to your MCP client configuration:

```json
{
  "axiomatic-annotations": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "axiomatic-annotations"],
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
  "axiomatic-annotations": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.annotations"],
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

### Academic Research

- **Literature Review**: Extract key findings, methodologies, and conclusions from research papers
- **Equation Analysis**: Identify and catalog mathematical formulations across multiple papers
- **Parameter Extraction**: Build databases of experimental parameters and their values
- **Citation Support**: Generate detailed annotations with precise page references

### Technical Documentation

- **Specification Analysis**: Extract technical requirements and parameters from engineering documents
- **Compliance Review**: Identify critical sections and requirements in regulatory documents
- **Knowledge Extraction**: Convert complex technical content into structured annotations
- **Image Analysis**: Analyze technical diagrams, charts, and schematics from image files
- **Documentation Review**: Process markdown and text documentation for key insights

### Educational Applications

- **Study Material Creation**: Generate comprehensive annotations for textbooks and papers
- **Concept Mapping**: Extract and organize key concepts with contextual explanations
- **Learning Support**: Create structured summaries of complex academic content

## Annotation Types

The server supports four primary annotation types:

1. **TEXT**: General textual content with contextual descriptions
2. **EQUATION**: Mathematical formulations in LaTeX format with parameter analysis
3. **FIGURE_DESCRIPTION**: Analysis and description of figures, charts, and diagrams
4. **PARAMETER**: Extracted parameter information with names, values, and units

## Best Practices

1. **Specific Queries**: Provide clear, focused instructions for better annotation quality
2. **Document Quality**: Use high-quality files for optimal content recognition (high-resolution images, clear PDFs, well-formatted text)
3. **Query Refinement**: Iterate on queries to extract different aspects of the same document
4. **File Format Selection**: Choose appropriate file formats based on content type (PDF for documents, PNG/JPEG for images, MD for structured text)

## Examples

See the [examples](https://github.com/Axiomatic-AI/ax-mcp/blob/main/examples/annotations/README.md) directory for examples of how to use the Axiomatic Annotations MCP server.

## Limitations

- Supports PDF, PNG, JPEG, Markdown, and text files only
- Requires internet connection for API access
- Processing time depends on document complexity and length
- File size limitations based on API constraints
- Page-specific annotations only available for PDF files

## Support

For issues or questions:

- GitHub Issues: https://github.com/axiomatic/ax-mcp/issues
- Email: developers@axiomatic.ai
