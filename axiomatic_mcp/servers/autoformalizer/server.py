"""Autoformalizer domain MCP server."""

import logging
import os
import sys
from typing import Annotated

import anthropic
from fastmcp import FastMCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Configure logging at module level
def setup_logging():
    """Set up logging configuration for the autoformalizer server."""
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Add file handler
    file_handler = logging.FileHandler("/tmp/mcp_autoformalizer_debug.log", mode="w")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Set up logging when module is imported
logger = setup_logging()

mcp = FastMCP(
    name="Autoformalizer",
    instructions="""The Autoformalizer server provides tools to transform natural language
        mathematical statements into Lean 4 theorem statements. Each generated theorem
        is returned in valid Lean syntax, with hypotheses formalized as parameters
        and the proof body replaced by a `sorry` placeholder. Use the lean_tools to help you 
        formalize the statement. Use lean_search and lean_loogle to search for the statement 
        in the project. Use lean_diagnostic_messages to check the file for any issues. The tool
        will automatically continue iterating until lean_diagnostic_messages reports no errors
        (or only acceptable 'sorry' warnings), ensuring the final result is a valid Lean theorem statement.""",
    version="0.0.1",
)


class AutoformalizerServer:
    def __init__(self):
        self.mcp = mcp

    def run(self):
        self.mcp.run()


def synthesize_claude_output(response):
    """Synthesize Claude output from response."""
    text_parts = []
    tool_parts = []

    for content in response.content:
        if hasattr(content, "text"):
            text_parts.append(content.text)
        elif content.type == "tool_use":
            tool_parts.append(content.name)

    claude_message = " ".join(text_parts)
    if tool_parts:
        claude_message += f" I will use tools: {', '.join(tool_parts)}"

    return claude_message


@mcp.tool(
    name="formalize_statement",
    description="""
                Translate a natural language mathematical statement into a Lean 4 theorem 
                declaration. The theorem is syntactically valid Lean, uses a descriptive snake_case name, 
                introduces hypotheses as parameters, and ends with `:= by sorry` to mark the missing proof.

    Available tools:
    - lean_file_contents: Read Lean files with line numbers
    - lean_run_code: Run complete Lean code snippets for testing
    - lean_diagnostic_messages: Get diagnostic messages for Lean files
    - lean_goal: Get proof goals at specific locations
    - lean_hover_info: Get documentation for Lean terms
    - lean_completions: Get code completions
    - lean_multi_attempt: Test multiple code approaches

    Workflow: Analyze query → Write lean theorem statement using lean_run_code → Verify with lean_diagnostic_messages. If there are issues, iterate until clean.
    Use lean_run_code to test your formalization before finalizing.
                """,
    tags=["lean", "formalization", "mathematics"],
)
async def formalize_statement(
    query: Annotated[str, "A natural language mathematical statement to formalize into Lean syntax"],
    file_path: Annotated[str, "Absolute path to Lean file to analyze and prove"],
    project_path: Annotated[str, "Path to the Lean project"] = "/Users/benjaminbreen/Desktop/ax-mcp/axiomatic_mcp/servers/leanclient/example",
    name: Annotated[str, "Agent name"] = "Autoformalizer",
    model: Annotated[str, "Claude model to use"] = "claude-sonnet-4-20250514",
    lean_tools_filter: Annotated[list[str] | None, "List of Lean tools to include (None = all tools)"] = None,
    max_iterations: Annotated[int, "Maximum tool use iterations"] = 100,
    max_tokens: Annotated[int, "Maximum tokens per API call"] = 5000,
) -> Annotated[str, "The corresponding Lean 4 theorem statement ending with `:= by sorry`"]:
    """Convert natural language mathematical statement to Lean theorem."""

    # Get OpenAI API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")

    # Use the module-level logger that's already configured

    logger.info(f"🔧 {name}: Start task")

    env = os.environ.copy()
    env["LEAN_PROJECT_PATH"] = project_path

    # Add elan bin directory to PATH so lake command can be found
    current_path = env.get("PATH", "")
    elan_path = "/Users/benjaminbreen/.elan/bin"
    if elan_path not in current_path:
        env["PATH"] = f"{elan_path}:{current_path}"

    # Initialize Lean Tools MCP server (our standalone version)
    lean_params = StdioServerParameters(
        command=sys.executable,  # Use current Python executable
        args=["-m", "axiomatic_mcp.servers.leanclient", "--transport", "stdio"],
        env=env,
    )

    try:
        # Connect to lean_tools server
        async with stdio_client(lean_params) as (lean_read, lean_write):
            async with ClientSession(lean_read, lean_write) as lean_session:
                # Initialize lean session
                await lean_session.initialize()

                # Get tools from lean server
                lean_tools = await lean_session.list_tools()

                logger.info(f"🔧 Lean tools: {[tool.name for tool in lean_tools.tools]}")

                client = anthropic.Anthropic(api_key=api_key)

                # Convert MCP tools to Claude format
                claude_tools = []

                # Add lean tools (filtered if specified)
                for tool in lean_tools.tools:
                    if lean_tools_filter is None or tool.name in lean_tools_filter:
                        claude_tools.append(
                            {
                                "name": tool.name,
                                "description": f"[Lean] {tool.description}",
                                "input_schema": tool.inputSchema,
                            }
                        )
                logger.info(f"✅ Total tools available to Claude: {len(claude_tools)}")
                logger.info(f"✅ Tool names: {[tool['name'] for tool in claude_tools]}")

                prompt = f"""Convert the following natural language mathematical statement into a Lean 4 theorem statement with a sorry placeholder.

    Natural language statement: {query}

    Please provide ONLY the Lean theorem statement in the following format:
    - Use proper Lean 4 syntax
    - Include appropriate theorem name (use snake_case)
    - Include necessary hypotheses as parameters
    -Import Mathlib
    - End with := by sorry
    - Do not include any explanations or additional text

    The general approach you must follow is:
    (1) Read the query and analyze what theorem statement you need to write
    (2) Formalize the query into a Lean theorem statement with proper imports
    (3) Use lean_run_code to test your formalization and check for syntax errors
    (4) If there are syntax issues, fix them and test again with lean_run_code
    (5) Once the syntax is correct, return the final Lean theorem statement

    For example, when working with this theorem:

    Example input: "If every prime greater than 2 is odd, then 7 must be odd. Is this true?"
    Example output: import Mathlib theorem seven_is_odd (h : ∀ p : ℕ, p > 2 ∧ Nat.Prime p → Odd p) : Odd 7 := by sorry

    Your response:"""

                messages = [{"role": "user", "content": prompt}]

                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=messages,
                    tools=claude_tools,
                )

                # append assistant's output to messages
                messages.append({"role": "assistant", "content": response.content})
                # append assistant's output to

                # get printable message
                claude_message = synthesize_claude_output(response)

                logger.info(f"🤖 {name} Claude: {claude_message}")

                # Handle multiple tool calls
                iteration = 0

                while response.stop_reason == "tool_use" and iteration < max_iterations:
                    iteration += 1
                    logger.info(f"🔄 {name} iteration {iteration}")

                    tool_results = []
                    for content in response.content:
                        if content.type == "tool_use":
                            logger.info(f"🔧 Using tool: {content.name}")
                            logger.info(f"📥 Input: {content.input}")

                            # Execute tool via lean server
                            result = await lean_session.call_tool(content.name, content.input)

                            if result.isError:
                                # Handle the error - something went wrong
                                logger.error("Tool failed")

                            logger.info(f"📤 Output: {result}")

                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": str(result.content),
                                }
                            )

                    messages.append({"role": "user", "content": tool_results})

                    response = client.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        messages=messages,
                        tools=claude_tools,
                    )

                    claude_message = synthesize_claude_output(response)

                    logger.info(f"🤖 {name} Claude: {claude_message}")

                    messages.append({"role": "assistant", "content": response.content})

                if iteration >= max_iterations:
                    logger.warning(f"⚠️ Maximum iterations reached. {name} may be incomplete.")

                # Extract the final response text
                final_response = ""
                for content in response.content:
                    if hasattr(content, "text"):
                        final_response += content.text

                logger.info(f"✅ {name}: Task completed successfully")

                return f"""MCPAgent Execution Result:

Agent: {name}
Model: {model}
Project: {project_path}
Iterations used: {iteration}/{max_iterations}

Final Response:
{final_response}

Tools available: {len(claude_tools)}
Lean tools filter: {lean_tools_filter or "None (all tools)"}"""

    except Exception as e:
        logger.error(f"❌ {name} error: {e!s}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback

        logger.error(f"❌ Full traceback: {traceback.format_exc()}")

        return f"MCPAgent error: {e!s}\n\nFull traceback:\n{traceback.format_exc()}"
