# Axiomatic MCP Servers

[![Static Badge](https://img.shields.io/badge/Join%20Discord-5865f2?style=flat)](https://discord.gg/KKU97ZR5)

MCP (Model Context Protocol) servers that provide AI assistants with access to the Axiomatic_AI Platform - a suite of advanced tools for scientific computing, document processing, and photonic circuit design.

## 🚀 Quickstart

#### 1. Check system requirements

- Python
  - Install [here](https://www.python.org/downloads/)
- uv
  - Install [here](https://docs.astral.sh/uv/getting-started/installation/)
  - Recommended not to install in conda (see [Troubleshooting](#troubleshooting))
- install extra packages (optional)
  - If you wish to use the AxPhotonicsPreview, you will need to install extra dependencies before continuing. After installing uv, run `uv tool install "axiomatic-mcp[pic]"`.

#### 2. Install your favourite client

[Cursor installation](https://cursor.com/docs/cli/installation)

#### 3. Get an API key

[![Static Badge](https://img.shields.io/badge/Get%20your%20API%20key-6EB700?style=flat)](https://docs.google.com/forms/d/e/1FAIpQLSfScbqRpgx3ZzkCmfVjKs8YogWDshOZW9p-LVXrWzIXjcHKrQ/viewform)

> You will receive an API key by email shortly after filling the form. Check your spam folder if it doesn't arrive.

#### 4. Install Axiomatic Operators (all except AxPhotonicsPreview)

<details>
<summary><strong>⚡ Claude Code</strong></summary>

```bash
claude mcp add axiomatic-mcp --env AXIOMATIC_API_KEY=your-api-key-here -- uvx --from axiomatic-mcp all
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
env = { AXIOMATIC_API_KEY = "your-api-key-here" }
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

> **Note:** This installs all tools except for AxPhotonicsPreview under one server. If you experience other issues, try [individual servers](#individual-servers) instead.

## Reporting Bugs

Found a bug? Please help us fix it by [creating a bug report](https://github.com/Axiomatic-AI/ax-mcp/issues/new?template=bug_report.md).

## Connect on Discord

Join our Discord to engage with other engineers and scientists using Axiomatic Operators. Ask for help, discuss bugs and features, and become a part of the Axiomatic community!

[![Static Badge](https://img.shields.io/badge/Join%20Discord-5865f2?style=flat)](https://discord.gg/KKU97ZR5)

## Troubleshooting

### Cannot install in Conda environment

It's not recommended to install axiomatic operators inside a conda environment. `uv` handles seperate python environments so it is safe to run "globally" without affecting your existing Python environments

### Server not appearing in Cursor

1. Restart Cursor after updating MCP settings
2. Check the Output panel (View → Output → MCP) for errors
3. Verify the command path is correct

### The "Add to cursor" button does not work

We have seen reports of the cursor window not opening correctly. If this happens you may manually add to cursor by:

1. Open cursor
2. Go to "Settings" > "Cursor Settings" > "MCP & Integration"
3. Click "New MCP Server"
4. Add the following configuration:

```
{
  "mcpServers": {
    "axiomatic-mcp": {
      "command": "uvx --from axiomatic-mcp all",
      "env": {
        "AXIOMATIC_API_KEY": "YOUR API KEY"
      },
      "args": []
    }
  }
}
```

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

## Individual servers

You may find more information about each server and how to install them individually in their own READMEs.

### 🖌️ [AxEquationExplorer](https://github.com/Axiomatic-AI/ax-mcp/tree/main/axiomatic_mcp/servers/equations/)

Compose equation of your interest based on information in the scientific paper.

### 📄 [AxDocumentParser](https://github.com/Axiomatic-AI/ax-mcp/tree/main/axiomatic_mcp/servers/documents/)

Convert PDF documents to markdown with advanced OCR and layout understanding.

### 📝 [AxDocumentAnnotator](https://github.com/Axiomatic-AI/ax-mcp/tree/main/axiomatic_mcp/servers/annotations/)

Create intelligent annotations for PDF documents with contextual analysis, equation extraction, and parameter identification.

### 🔬 [AxPhotonicsPreview](https://github.com/Axiomatic-AI/ax-mcp/tree/main/axiomatic_mcp/servers/pic/)

Design photonic integrated circuits using natural language descriptions. Additional requirements are needed, please refer to [Check system requirements](#1-check-system-requirements)

### 📊 [AxPlotToData](https://github.com/Axiomatic-AI/ax-mcp/tree/main/axiomatic_mcp/servers/plots/)

Extract numerical data from plot images for analysis and reproduction.

## Requesting Features

Have an idea for a new feature? We'd love to hear it! [Submit a feature request](https://github.com/Axiomatic-AI/ax-mcp/issues/new?template=feature_request.md) and:

- Describe the problem your feature would solve
- Explain your proposed solution
- Share any alternatives you've considered
- Provide specific use cases

## Support

- **Join our [Discord Server](https://discord.gg/KKU97ZR5)**
- **Issues**: [GitHub Issues](https://github.com/Axiomatic-AI/ax-mcp/issues)
