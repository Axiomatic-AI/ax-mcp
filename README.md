# Axiomatic MCP Servers

[![Static Badge](https://img.shields.io/badge/Join%20Discord-5865f2?style=flat)](https://discord.gg/KKU97ZR5)

MCP (Model Context Protocol) servers that provide AI assistants with access to the Axiomatic_AI Platform - a suite of advanced tools for scientific computing, document processing, and photonic circuit design.

## 🚀 Quickstart

### System requirements

- Python
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

#### 1. Get an API key

[![Static Badge](https://img.shields.io/badge/Get%20your%20API%20key-6EB700?style=flat)](https://docs.google.com/forms/d/e/1FAIpQLSfScbqRpgx3ZzkCmfVjKs8YogWDshOZW9p-LVXrWzIXjcHKrQ/viewform)

#### 2. Configure your client

<details>
<summary><strong>⚡ Claude Code</strong></summary>

```bash
claude mcp add axiomatic-mcp --command "uvx --from axiomatic-mcp all" --env AXIOMATIC_API_KEY=your-api-key-here
```

</details>

<details>
<summary><strong>🔷 Cursor</strong></summary>

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=axiomatic-mcp&config=eyJjb21tYW5kIjoidXZ4IC0tZnJvbSBheGlvbWF0aWMtbWNwIGFsbCIsImVudiI6eyJBWElPTUFUSUNfQVBJX0tFWSI6InlvdXItYXBpLWtleS1oZXJlIn19)

</details>

<details>
<summary><strong>🤖 Claude Desktop</strong></summary>

1. Open Claude Desktop settings → Developer → Edit MCP config
2. Add this configuration:

```json
{
  "mcpServers": {
    "axiomatic-mcp": {
      "command": "uvx",
      "args": ["--from", "axiomatic-mcp", "all"],
      "env": {
        "AXIOMATIC_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

3. Restart Claude Desktop

</details>

<details>
<summary><strong>🔮 Gemini CLI</strong></summary>

Follow the MCP install guide and use the standard configuration above.  
See the official instructions here: [Gemini CLI MCP Server Guide](https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md#configure-the-mcp-server-in-settingsjson)

```json
{
  "axiomatic-mcp": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "all"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

</details>

<details>
<summary><strong>🌬️ Windsurf</strong></summary>

Follow the [Windsurf MCP documentation](https://docs.windsurf.com/windsurf/cascade/mcp).  
Use the standard configuration above.

```json
{
  "axiomatic-mcp": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp", "all"],
    "env": {
      "AXIOMATIC_API_KEY": "your-api-key-here"
    }
  }
}
```

</details>

<details>
<summary><strong>🧪 LM Studio</strong></summary>

#### Click the button to install:

[![Install MCP Server](https://files.lmstudio.ai/deeplink/mcp-install-light.svg)](https://lmstudio.ai/install-mcp?name=axiomatic-mcp&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJheGlvbWF0aWMtbWNwIiwiYWxsIl19)

> **Note:** After installing via the button, open LM Studio MCP settings and add:
>
> ```json
> "env": {
>   "AXIOMATIC_API_KEY": "your-api-key-here"
> }
> ```

</details>

<details>
<summary><strong>💻 Codex</strong></summary>

Create or edit the configuration file `~/.codex/config.toml` and add:

```toml
[mcp_servers.axiomatic-mcp]
command = "uvx"
args = ["--from", "axiomatic-mcp", "all"]
```

For more information, see the [Codex MCP documentation](https://github.com/openai/codex/blob/main/codex-rs/config.md#mcp_servers)

</details> 
<details>
<summary><strong>🌊 Other MCP Clients</strong></summary>

Use this server configuration:

```json
{
  "command": "uvx",
  "args": ["--from", "axiomatic-mcp", "all"],
  "env": {
    "AXIOMATIC_API_KEY": "your-api-key-here"
  }
}
```

</details>

> **Note:** This installs all tools under one server and may cause issues with some clients. If you experience problems, install individual servers instead.

## Individual servers

You may find more information about each server and how to install them individually in their own READMEs.

### 🖌️ [AxEquationExplorer](https://github.com/Axiomatic-AI/ax-mcp/tree/main/axiomatic_mcp/servers/equations/)

Compose equation of your interest based on information in the scientific paper.

### 📄 [AxDocumentParser](https://github.com/Axiomatic-AI/ax-mcp/tree/main/axiomatic_mcp/servers/documents/)

Convert PDF documents to markdown with advanced OCR and layout understanding.

### 📝 [AxDocumentAnnotator](https://github.com/Axiomatic-AI/ax-mcp/tree/main/axiomatic_mcp/servers/annotations/)

Create intelligent annotations for PDF documents with contextual analysis, equation extraction, and parameter identification.

### ⚙️ [AxModelFitter](https://github.com/Axiomatic-AI/ax-mcp/tree/main/axiomatic_mcp/servers/axmodelfitter/)

Fit parametric models or digital twins to observational data using advanced statistical analysis and optimization algorithms.

### 🔬 [AxPhotonicsPreview](https://github.com/Axiomatic-AI/ax-mcp/tree/main/axiomatic_mcp/servers/pic/)

Design photonic integrated circuits using natural language descriptions.

### 📊 [AxPlotToData](https://github.com/Axiomatic-AI/ax-mcp/tree/main/axiomatic_mcp/servers/plots/)

Extract numerical data from plot images for analysis and reproduction.

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

### Tools not appearing

If you experience any issues such as tools not appearing, it may be that you are using an old version and need to clear uv's cache to update it.

```bash
uv cache clean
```

Then restart your MCP client (e.g. restart Cursor).

This clears the uv cache and forces fresh downloads of packages on the next run.

## Contributing

We welcome contributions from the community! Here's how you can help:

### Submitting Pull Requests

We love pull requests! If you'd like to contribute code:

1. Fork the repository
2. Create a new branch for your feature or fix
3. Make your changes and test them thoroughly
4. Submit a pull request with a clear description of your changes
5. Reference any related issues in your PR description

### Reporting Bugs

Found a bug? Please help us fix it by [creating a bug report](https://github.com/Axiomatic-AI/ax-mcp/issues/new?template=bug_report.md). When reporting bugs:

- Use the bug report template to provide all necessary information
- Include steps to reproduce the issue
- Add relevant error messages and logs
- Specify your environment details (OS, Python version, etc.)

### Requesting Features

Have an idea for a new feature? We'd love to hear it! [Submit a feature request](https://github.com/Axiomatic-AI/ax-mcp/issues/new?template=feature_request.md) and:

- Describe the problem your feature would solve
- Explain your proposed solution
- Share any alternatives you've considered
- Provide specific use cases

### Quick Links

- 🐛 [Report a Bug](https://github.com/Axiomatic-AI/ax-mcp/issues/new?template=bug_report.md)
- 💡 [Request a Feature](https://github.com/Axiomatic-AI/ax-mcp/issues/new?template=feature_request.md)
- 📋 [View All Issues](https://github.com/Axiomatic-AI/ax-mcp/issues)
- 💬 [Discord Server](https://discord.gg/KKU97ZR5)

## Support

- **Join our [Discord Server](https://discord.gg/KKU97ZR5)**
- **Issues**: [GitHub Issues](https://github.com/Axiomatic-AI/ax-mcp/issues)
- **Email**: developers@axiomatic-ai.com
