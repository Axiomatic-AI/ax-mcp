# Lean Client MCP Server

An advanced Lean 4 MCP (Model Context Protocol) server that provides comprehensive LSP integration for interactive theorem proving and Lean development.

## Features

- **Real-time Diagnostics**: Get compilation errors, warnings, and info messages
- **Interactive Goal States**: View proof goals and context at any position
- **Hover Documentation**: Access detailed documentation and type information
- **Term Goals**: Inspect expected types at specific locations
- **Multi-attempt Testing**: Try multiple proof tactics simultaneously
- **File Operations**: Read, write, and analyze Lean files
- **LSP Integration**: Full Language Server Protocol support

## Prerequisites

### 1. Lean 4 Installation

First, install Lean 4 using elan:

```bash
# Install elan (Lean version manager)
curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh

# Install Lean 4
elan default leanprover/lean4:v4.16.0
```

### 2. Set Up a Lean Project

Create a new Lean project with Mathlib:

```bash
# Create a new project
lake new my_lean_project
cd my_lean_project

# Add Mathlib dependency
echo '[[require]]
name = "mathlib"
scope = "leanprover-community"
rev = "v4.16.0"' >> lakefile.toml

# Build the project (this may take several minutes)
lake update && lake build
```

**Note**: If you already have a working Lean project, you can use that instead.

### 3. Get the Project Path

Note the absolute path to your Lean project directory:
```bash
# Get current directory path
pwd
# Example output: /Users/username/my_lean_project
```

## Installation & Configuration

### Using uvx (Recommended)

```bash
uvx --from "axiomatic-mcp[lean]" axiomatic-leanclient
```

### MCP Configuration

Add to your MCP settings file (`.cursor/mcp.json`):

```json
{
  "axiomatic-leanclient": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp[lean]", "axiomatic-leanclient"],
    "env": {
      "LEAN_PROJECT_PATH": "/path/to/your/lean/project"
    }
  }
}
```

#### For Development

First, install the lean dependencies:

```bash
pip install "axiomatic-mcp[lean]"
```

Then configure MCP:

```json
{
  "axiomatic-leanclient": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.leanclient"],
    "env": {
      "LEAN_PROJECT_PATH": "/path/to/your/lean/project"
    }
  }
}
```

**Environment Variables:**
- `LEAN_PROJECT_PATH`: Path to your Lean project directory (Required)

**Requirements:**
- The `leanclient` Python package (installed with `[lean]` extra)  
- Lean 4 installation (for LSP functionality)

## Usage Examples

The included `example.lean` file demonstrates a theorem about the order of elements in additive groups. Here's how to use the MCP tools with it:

### 1. Read File Contents

```python
# Returns the full file with line numbers
lean_file_contents("/path/to/example.lean", annotate_lines=True)
```

**Output**: Complete file contents with line numbers (1-62 lines)

### 2. Check Diagnostics

```python
# Get compilation errors and warnings
lean_diagnostic_messages("/path/to/example.lean")
```

**Example Output**:
```
l50c9-l50c33, severity: 1
unknown constant 'ZMod.natCast_eq_zero_iff'

l50c9-l50c33, severity: 1
tactic 'rewrite' failed, equality or iff proof expected
```

### 3. Inspect Proof Goals

```python
# View goals at line 42 (inside the proof)
lean_goal("/path/to/example.lean", line=42)
```

**Example Output**:
```
Before:
⊢ ¬↑(k * 6) = 0

After:
⊢ k * 6 < 36
```

### 4. Get Documentation

```python
# Hover over 'addOrderOf_eq_iff' at line 56
lean_hover_info("/path/to/example.lean", line=56, column=8)
```

**Example Output**:
```
addOrderOf_eq_iff: addOrderOf x = n ↔ n • x = 0 ∧ ∀ m < n, 0 < m → m • x ≠ 0
```

### 5. Check Term Types

```python
# Get expected type at a specific position
lean_term_goal("/path/to/example.lean", line=14)
```

### 6. Test Multiple Tactics

```python
# Try different approaches for line 50
lean_multi_attempt("/path/to/example.lean", line=50, snippets=[
    "rw [ZMod.int_cast_eq_zero_iff]",
    "rw [ZMod.cast_nat_cast]", 
    "simp [ZMod.nat_cast_eq_zero_iff_dvd]"
])
```

## Working with the Example

The `example.lean` file contains:

1. **Imports**: Essential Mathlib modules for group theory and number theory
2. **Definitions**: 
   - `RootsOfUnity`: Complex roots of unity
   - `QSqrt2`: Rational numbers extended with √2
3. **Theorem**: `order_of_6_zmod36` - proves that 6 has order 6 in ℤ/36ℤ

### Debugging the Proof

The theorem has intentional errors to demonstrate diagnostic capabilities:

- **Line 50**: Uses incorrect constant name `ZMod.natCast_eq_zero_iff`
- **Solution**: Use the multi-attempt tool to test corrections

### Interactive Development Workflow

1. **Read** the file to understand the structure
2. **Check diagnostics** to identify errors
3. **Inspect goals** at proof steps to understand what needs to be proven
4. **Use hover** to get documentation for unfamiliar functions
5. **Test alternatives** with multi-attempt when stuck

## System Requirements

- **Lean 4**: Installed and accessible in PATH
- **Python**: 3.10 or higher
- **leanclient**: Automatically installed with `[lean]` extra
- **Mathlib**: For the example file (handled by Lean project)

## Environment Variables

- `LEAN_PROJECT_PATH`: Path to your Lean project root (optional)
- `ANTHROPIC_API_KEY`: Not required for basic functionality

## Troubleshooting

### Server Won't Start
- Ensure `leanclient` is installed: `pip install leanclient>=0.1.0`
- Check that Lean 4 is in your PATH: `lean --version`

### Diagnostics Not Working
- Verify the file path is absolute
- Ensure the Lean file is in a proper Lean project (with `lakefile.lean`)

### No Hover Information
- Make sure you're pointing to a valid identifier
- Use correct line/column positions (1-indexed)

## Available Tools

| Tool | Description |
|------|-------------|
| `lean_file_contents` | Read Lean files with optional line numbers |
| `lean_diagnostic_messages` | Get compilation errors and warnings |
| `lean_goal` | View proof goals at specific positions |
| `lean_term_goal` | Get expected types at cursor positions |
| `lean_hover_info` | Access documentation and type information |
| `lean_multi_attempt` | Test multiple proof approaches |
| `lean_declaration_file` | Find where symbols are declared |

## Contributing

This MCP server is part of the axiomatic-mcp package. See the main README for contribution guidelines.

## License

MIT License - see the main project for details.
