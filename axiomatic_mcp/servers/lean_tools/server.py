"""Standalone Lean Tools MCP Server using FastMCP."""

import os
import subprocess
import tempfile
import json
from typing import List, Dict, Optional, Annotated
import requests

from fastmcp import FastMCP

mcp = FastMCP(
    name="Lean Tools",
    instructions="""A collection of Lean theorem proving tools for working with Lean 4 files.
    These tools provide diagnostic information, goal states, file operations, and theorem search capabilities.""",
    version="0.1.0"
)


@mcp.tool("lean_file_contents")
def lean_file_contents(
    file_path: Annotated[str, "Absolute path to the Lean file"],
    annotate_lines: Annotated[bool, "Whether to add line numbers"] = True
) -> Annotated[str, "File contents, optionally with line numbers"]:
    """Get the contents of a Lean file, optionally with line numbers."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if annotate_lines:
            lines = content.split('\n')
            max_digits = len(str(len(lines)))
            annotated_lines = []
            for i, line in enumerate(lines, 1):
                padding = ' ' * (max_digits - len(str(i)))
                annotated_lines.append(f"{i}{padding}: {line}")
            return '\n'.join(annotated_lines)
        else:
            return content
            
    except FileNotFoundError:
        return f"File `{file_path}` does not exist. Please check the path and try again."
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool("lean_write_file")
def lean_write_file(
    file_path: Annotated[str, "Absolute path to the Lean file"],
    content: Annotated[str, "Content to write to the file"]
) -> Annotated[str, "Result of write operation"]:
    """Write content to a Lean file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool("lean_diagnostic_messages")
def lean_diagnostic_messages(
    file_path: Annotated[str, "Absolute path to the Lean file"]
) -> Annotated[List[str], "List of diagnostic messages (errors, warnings, info)"]:
    """Get diagnostic messages for a Lean file."""
    try:
        # Use lean to check the file
        result = subprocess.run(
            ["lean", file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        diagnostics = []
        
        if result.returncode != 0 and result.stdout:
            # Parse stdout for diagnostic messages (Lean 4 puts errors in stdout)
            lines = result.stdout.split('\n')
            current_diagnostic = []
            
            for line in lines:
                if line.strip():
                    if line.startswith(file_path) or '://' in line:
                        if current_diagnostic:
                            diagnostics.append('\n'.join(current_diagnostic))
                            current_diagnostic = []
                        current_diagnostic.append(line)
                    elif current_diagnostic:
                        current_diagnostic.append(line)
            
            if current_diagnostic:
                diagnostics.append('\n'.join(current_diagnostic))
        
        return diagnostics
        
    except subprocess.TimeoutExpired:
        return ["Error: Lean command timed out"]
    except Exception as e:
        return [f"Error getting diagnostics: {str(e)}"]


@mcp.tool("lean_run_code")
def lean_run_code(
    code: Annotated[str, "Lean code to run"]
) -> Annotated[str, "Result of running the Lean code"]:
    """Run Lean code and return the result."""
    try:
        # Create a temporary file with the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lean', delete=False, encoding='utf-8') as f:
            # Add import if not present
            if 'import' not in code:
                f.write('import Mathlib\n\n')
            f.write(code)
            temp_file = f.name
        
        try:
            # Check the file with Lean
            result = subprocess.run(
                ["lean", temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return "Code compiled successfully with no errors."
            else:
                # Lean 4 puts errors in stdout, not stderr
                output = result.stdout if result.stdout else result.stderr
                return f"Lean output:\n{output}"
                
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass
                
    except Exception as e:
        return f"Error running code: {str(e)}"



@mcp.tool("lean_multi_attempt")
def lean_multi_attempt(
    file_path: Annotated[str, "Absolute path to the Lean file"],
    line: Annotated[int, "Line number to replace"],
    snippets: Annotated[List[str], "List of proof attempts to try"]
) -> Annotated[str, "Results of trying multiple proof snippets"]:
    """Try multiple proof snippets and return results."""
    try:
        with open(file_path, 'r') as f:
            original_lines = f.readlines()
        
        if line > len(original_lines):
            return f"Line {line} is beyond the end of file"
        
        results = []
        
        for i, snippet in enumerate(snippets):
            try:
                # Create modified content
                modified_lines = original_lines.copy()
                modified_lines[line - 1] = snippet + '\n'
                modified_content = ''.join(modified_lines)
                
                # Write to temp file and test
                with tempfile.NamedTemporaryFile(mode='w', suffix='.lean', delete=False) as f:
                    f.write(modified_content)
                    temp_file = f.name
                
                try:
                    result = subprocess.run(
                        ["lean", temp_file],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        results.append(f"Attempt {i+1}: SUCCESS - '{snippet}'")
                    else:
                        # Lean 4 puts errors in stdout
                        error_msg = result.stdout.strip() if result.stdout else result.stderr.strip()
                        results.append(f"Attempt {i+1}: FAILED - '{snippet}' - {error_msg[:200]}...")
                        
                finally:
                    try:
                        os.unlink(temp_file)
                    except:
                        pass
                        
            except Exception as e:
                results.append(f"Attempt {i+1}: ERROR - '{snippet}' - {str(e)}")
        
        return '\n'.join(results)
        
    except Exception as e:
        return f"Error in multi-attempt: {str(e)}"


@mcp.tool("lean_leansearch")  
def lean_leansearch(
    query: Annotated[str, "Search query for theorems and lemmas"]
) -> Annotated[str, "Search results from LeanSearch API"]:
    """Search for Lean theorems and lemmas using LeanSearch."""
    try:
        import urllib.request
        
        headers = {"User-Agent": "lean-lsp-mcp/0.1", "Content-Type": "application/json"}
        payload = json.dumps(
            {"num_results": "5", "query": [query]}
        ).encode("utf-8")

        req = urllib.request.Request(
            "https://leansearch.net/search",
            data=payload,
            headers=headers,
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            results = json.loads(response.read().decode("utf-8"))

        if not results or not results[0]:
            return "No results found."
        results = results[0][:5]
        results = [r["result"] for r in results]

        for result in results:
            result.pop("docstring", None)  # Remove docstring if present
            if "module_name" in result:
                result["module_name"] = ".".join(result["module_name"])
            if "name" in result:
                result["name"] = ".".join(result["name"])

        # Format results nicely
        formatted_results = []
        for result in results:
            formatted_results.append(json.dumps(result, indent=2))
        
        return '\n'.join(formatted_results)

    except Exception as e:
        return f"leansearch error:\n{str(e)}"


@mcp.tool("lean_loogle")
def lean_loogle(
    query: Annotated[str, "Type signature query for Loogle search"]
) -> Annotated[str, "Search results from Loogle API"]:
    """Search for Lean lemmas by type signature using Loogle."""
    try:
        import urllib.request
        import urllib.parse
        
        req = urllib.request.Request(
            f"https://loogle.lean-lang.org/json?q={urllib.parse.quote(query)}",
            headers={"User-Agent": "lean-lsp-mcp/0.1"},
            method="GET",
        )

        with urllib.request.urlopen(req, timeout=20) as response:
            results = json.loads(response.read().decode("utf-8"))

        if "hits" not in results:
            return "No results found."

        results = results["hits"][:5]
        for result in results:
            result.pop("doc", None)  # Remove doc field if present
        
        # Format results nicely
        formatted_results = []
        for result in results:
            formatted_results.append(json.dumps(result, indent=2))
        
        return '\n'.join(formatted_results)
        
    except Exception as e:
        return f"loogle error:\n{str(e)}"


@mcp.tool("lean_build")
def lean_build(
    project_path: Annotated[str, "Path to Lean project"],
    clean: Annotated[bool, "Whether to run lake clean first"] = False
) -> Annotated[str, "Build output"]:
    """Build a Lean project using lake."""
    try:
        output_lines = []
        
        if clean:
            result = subprocess.run(
                ["lake", "clean"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            output_lines.append(f"Lake clean: {result.stdout}{result.stderr}")
        
        result = subprocess.run(
            ["lake", "build"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            output_lines.append(f"Build successful: {result.stdout}")
        else:
            output_lines.append(f"Build failed: {result.stderr}")
        
        return '\n'.join(output_lines)
        
    except Exception as e:
        return f"Error building project: {str(e)}"


def main():
    """Main entry point for the lean_tools server."""
    import sys
    
    # Handle command line arguments for MCP transport
    if len(sys.argv) > 1 and sys.argv[1] == "--transport" and len(sys.argv) > 2 and sys.argv[2] == "stdio":
        mcp.run()
    else:
        mcp.run()


if __name__ == "__main__":
    main()