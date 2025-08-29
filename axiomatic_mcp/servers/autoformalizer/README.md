# Axiomatic Autoformalizer Server

An advanced MCP (Model Context Protocol) server that automatically translates natural language mathematical statements into syntactically correct Lean 4 theorem declarations.

## Overview

The Autoformalizer server enables AI assistants and mathematicians to convert informal mathematical statements into formal Lean 4 code. It leverages frontier models reasoning capabilities with comprehensive Lean tools to iteratively refine formalizations until they compile correctly.

## Features

- **Natural Language Processing**: Converts informal mathematical statements to Lean syntax
- **Intelligent Search**: Uses leansearch and loogle to find existing related theorems
- **Syntax Validation**: Automatically tests and fixes Lean compilation errors
- **Iterative Refinement**: Continuously improves formalization until syntactically correct
- **File Management**: Writes formalized theorems to specified Lean files
- **Comprehensive Tool Access**: Integrates with full Lean LSP capabilities

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

## Installation & Configuration

### Quick Install (via PyPI)

Add to your MCP client configuration:

```json
{
  "axiomatic-autoformalizer": {
    "command": "uvx",
    "args": ["--from", "axiomatic-mcp[lean]", "axiomatic-autoformalizer"],
    "env": {
      "ANTHROPIC_API_KEY": "your-anthropic-api-key-here",
      "LEAN_PROJECT_PATH": "/path/to/your/lean/project"
    }
  }
}
```

### Development Install

First, install the lean dependencies:

```bash
pip install "axiomatic-mcp[lean]"
```

Then configure MCP:

```json
{
  "axiomatic-autoformalizer": {
    "command": "python",
    "args": ["-m", "axiomatic_mcp.servers.autoformalizer"],
    "env": {
      "ANTHROPIC_API_KEY": "your-anthropic-api-key-here",
      "LEAN_PROJECT_PATH": "/path/to/your/lean/project"
    }
  }
}
```

## Configuration

### Required Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude access (required)
- `LEAN_PROJECT_PATH`: Path to your Lean project directory (optional, can be provided per call)

## Tools Available

### `formalize_statement`

Translates a natural language mathematical statement into a Lean 4 theorem declaration.

**Arguments:**
- `query`: Natural language mathematical statement to formalize
- `file_path`: Absolute path where the formalized theorem should be saved
- `project_path`: Path to the Lean project (optional, defaults to environment variable)
- `model`: Claude model to use (default: "claude-sonnet-4-20250514")
- `max_iterations`: Maximum tool use iterations (default: 100)
- `max_tokens`: Maximum tokens per API call (default: 5000)

**Returns:**
- Syntactically correct Lean 4 theorem statement ending with `:= by sorry`
- Execution statistics and tool usage information

## Usage Examples

### 1. Basic Mathematical Statement

```python
# Formalize a simple mathematical statement
formalize_statement(
    query="Show that if a unitary matrix satisfies U^2 = U then U = 1",
    file_path="/path/to/your/theorem.lean"
)
```

**Output**: 
```lean
import Mathlib

theorem unitary_idempotent_is_identity {n : ℕ} (U : Matrix (Fin n) (Fin n) ℂ) 
  (h_unitary : U * U.conjTranspose = 1) (h_idempotent : U ^ 2 = U) : U = 1 := by sorry
```

### 2. Number Theory Statement

```python
# Formalize a number theory result
formalize_statement(
    query="Prove that the square root of 2 is irrational",
    file_path="/path/to/sqrt2_irrational.lean"
)
```

**Output**:
```lean
import Mathlib

theorem sqrt_two_irrational : Irrational (Real.sqrt 2) := by sorry
```

### 3. Group Theory Statement

```python
# Formalize a group theory theorem
formalize_statement(
    query="Show that every finite group of prime order is cyclic",
    file_path="/path/to/prime_order_cyclic.lean"
)
```

**Output**:
```lean
import Mathlib

theorem finite_group_prime_order_is_cyclic (G : Type*) [Group G] [Fintype G] 
  (p : ℕ) [hp : Fact (Nat.Prime p)] (h : Fintype.card G = p) : IsCyclic G := by sorry
```

## Workflow

The autoformalizer follows an intelligent 8-step process:

1. **Analyze** the natural language mathematical statement
2. **Search** for existing related theorems using `lean_leansearch` and `lean_loogle`
3. **Formalize** the statement into Lean syntax based on search results
4. **Test** the formalization using `lean_run_code` for syntax validation
5. **Iterate** to fix any syntax errors found during testing
6. **Save** the corrected formalization to the target file using `lean_write_file`
7. **Verify** the saved file using `lean_diagnostic_messages`
8. **Return** the final syntactically correct theorem statement

## Available Lean Tools

The autoformalizer has access to a comprehensive set of 13 Lean tools:

### Core Tools
- `lean_file_contents` - Read Lean files with line numbers
- `lean_write_file` - Write content to Lean files
- `lean_diagnostic_messages` - Get compilation errors and warnings
- `lean_goal` - View proof goals at specific positions
- `lean_hover_info` - Get documentation for Lean terms
- `lean_completions` - Get code completions
- `lean_multi_attempt` - Test multiple code approaches
- `lean_run_code` - Run complete Lean code snippets

### Search Tools
- `lean_leansearch` - Search for theorems using natural language
- `lean_loogle` - Search for definitions by type signature
- `lean_state_search` - Search theorems based on proof state

### Analysis Tools
- `lean_term_goal` - Get expected types at cursor positions
- `lean_declaration_file` - Find where symbols are declared

## Best Practices

1. **Clear Statements**: Provide precise mathematical statements for better formalization
2. **Context**: Include necessary mathematical context (e.g., "in a topological space")
3. **Existing Work**: The tool will automatically search for related existing theorems
4. **Iteration**: Allow the tool to iterate - complex statements may require multiple refinements
5. **Project Setup**: Ensure your Lean project has proper Mathlib dependencies

## Limitations

- Requires valid Lean 4 project with Mathlib for complex mathematical statements
- Performance depends on Claude API availability and rate limits
- Very advanced mathematical concepts may require manual refinement
- Generated theorems include `sorry` placeholders - proofs must be completed separately

## System Requirements

- **Lean 4**: Installed and accessible in PATH
- **Python**: 3.10 or higher
- **leanclient**: Automatically installed with `[lean]` extra
- **Mathlib**: Required for most mathematical formalizations
- **Anthropic API**: Access to Claude models

## Troubleshooting

### Server Won't Start
- Ensure `ANTHROPIC_API_KEY` is set correctly
- Check that `leanclient` is installed: `pip install "axiomatic-mcp[lean]"`
- Verify Lean 4 is in your PATH: `lean --version`

### Formalization Fails
- Check that the Lean project path is correct and accessible
- Ensure Mathlib is properly built in the target project
- Verify the mathematical statement is clearly expressed

### Syntax Errors Persist
- The tool automatically iterates to fix syntax errors
- If issues persist after max iterations, the statement may be too complex
- Try breaking complex statements into simpler parts

## Performance

Typical performance metrics:
- **Simple statements**: 3-7 iterations, ~30-60 seconds
- **Moderate complexity**: 8-15 iterations, ~1-3 minutes  
- **Complex statements**: 15-30 iterations, ~3-8 minutes

## Contributing

This MCP server is part of the axiomatic-mcp package. See the main README for contribution guidelines.

## License

MIT License - see the main project for details.

## Support

For issues or questions:

- GitHub Issues: [Axiomatic MCP Issues](https://github.com/Axiomatic-AI/ax-mcp/issues)
- Email: [developers@axiomatic-ai.com](mailto:developers@axiomatic-ai.com)

## Related Resources

- [Lean 4 Documentation](https://lean-lang.org/)
- [Mathlib Documentation](https://leanprover-community.github.io/mathlib4_docs/)
- [Lean Community](https://leanprover.zulipchat.com/)
