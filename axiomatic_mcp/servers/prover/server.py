"""Prover domain MCP server."""

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
    """Set up logging configuration for the prover server."""
    # Create logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Add file handler
    file_handler = logging.FileHandler("/tmp/mcp_prover_debug.log", mode="w")
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
    name="Prover",
    instructions="""The Prover server provides tools to complete Lean theorem proofs.
        It takes incomplete Lean theorems and uses available Lean tools to iteratively
        complete the proofs. Use the leanclient tools to help you complete the proof.
        Use lean_diagnostic_messages to check the file for any issues. The tool
        will automatically continue iterating until lean_diagnostic_messages reports no errors
        (or only acceptable 'sorry' warnings), ensuring the final result is a complete proof.""",
    version="0.0.1",
)


class ProverServer:
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
    name="mcp_agent_execute",
    description="""Execute MCPAgent to work with Lean files and prove theorems. Uses file-based workflow with available Lean tools.

    Available tools (13 total):
    From leanclient (13 tools):
    - lean_file_contents: Read Lean files with line numbers
    - lean_write_file: Write content to Lean files (save proof solutions)
    - lean_run_code: Run complete Lean code snippets for testing
    - lean_diagnostic_messages: Get diagnostic messages for Lean files
    - lean_goal: Get proof goals at specific locations
    - lean_hover_info: Get documentation for Lean terms
    - lean_completions: Get code completions
    - lean_declaration_file: Get file contents where symbols are declared
    - lean_multi_attempt: Test multiple code approaches
    - lean_leansearch: Search for theorems using natural language
    - lean_loogle: Search for definitions by type signature
    - lean_state_search: Search theorems based on proof state
    - lean_term_goal: Get expected type at specific location

    Workflow: Read file → Check goals at positions → Write improved proof → Verify with diagnostics. Use search tools when stuck.
    """,
    tags=["lean", "proving", "mcp", "agent"],
)
async def mcp_agent_execute(
    file_path: Annotated[str, "Absolute path to Lean file to analyze and prove"],
    project_path: Annotated[str, "Path to the Lean project"] = "/Users/jacobmccarran_ax/ax-mcp/my_lean_project",
    name: Annotated[str, "Agent name"] = "Prover",
    model: Annotated[str, "Claude model to use"] = "claude-sonnet-4-20250514",
    lean_client_filter: Annotated[list[str] | None, "List of Lean client tools to include (None = all tools)"] = None,
    max_iterations: Annotated[int, "Maximum tool use iterations"] = 100,
    max_tokens: Annotated[int, "Maximum tokens per API call"] = 5000,
) -> Annotated[str, "Agent execution result"]:
    """Execute MCPAgent with Lean tools to prove theorems in a Lean file."""

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")

    # Setup logging with file output
    logger = logging.getLogger(__name__)

    # Configure logging to file if not already configured - overwrite each time
    if not logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("/tmp/mcp_prover_debug.log", mode="w"), logging.StreamHandler()],
        )

    # Agent configuration

    logger.info(f"🔧 {name}: Start task")

    env = os.environ.copy()
    env["LEAN_PROJECT_PATH"] = project_path

    # Initialize Lean Client MCP server (13 tools)
    lean_client_params = StdioServerParameters(
        command=sys.executable,  # Use current Python executable
        args=["-m", "axiomatic_mcp.servers.leanclient", "--transport", "stdio"],
        env=env,
    )

    try:
        # Connect to leanclient server
        async with (
            stdio_client(lean_client_params) as (lean_client_read, lean_client_write),
            ClientSession(lean_client_read, lean_client_write) as lean_client_session,
        ):
            # Initialize session
            await lean_client_session.initialize()

            # Get tools from leanclient server
            lean_client_tools = await lean_client_session.list_tools()

            logger.info(f"🔧 Lean client tools: {[tool.name for tool in lean_client_tools.tools]}")

            client = anthropic.Anthropic(api_key=api_key)

            # Convert MCP tools to Claude format
            claude_tools = []

            # Add lean client tools (filtered if specified)
            for tool in lean_client_tools.tools:
                if lean_client_filter is None or tool.name in lean_client_filter:
                    claude_tools.append(
                        {
                            "name": tool.name,
                            "description": f"[Lean Client] {tool.description}",
                            "input_schema": tool.inputSchema,
                        }
                    )

            logger.info(f"✅ Total tools available to Claude: {len(claude_tools)}")
            logger.info(f"✅ Tool names: {[tool['name'] for tool in claude_tools]}")

            # Create initial message with file path
            prompt = f"""You are an expert Lean theorem prover. You need to work with the Lean file at: {file_path}

The general approach you must follow is:
(1) Read the file content and analyze what theorems need to be proven
(2) Run lean_diagnostic_messages to check the current state  
(3) Look at the theorem and identify proofs with 'sorry'
(4) Produce an initial sketch of the proof: a high-level outline of the proof steps without any specific tactics.
For example, when working with this theorem:

-- theorem statement
theorem SlidingBlockProblem_2
-- Variables
(Ei Ef h g m v : ℝ)

-- Hypotheses
(h_initial : Ei = m * g * h)
(h_final : Ef = (1 / 2) * m * v^2)
(h_conservation : Ei = Ef)
(hm : 0 < m)
(hv : 0 < v)
(hg : g = 10)
(hh : h = 10)
:

-- Objective
v = 10 * √2 := by
sorry

You must produce this output:

-- Step 1: Ei = Ef
have h1 : Ei = Ef := by
  sorry

-- Step 2: m * g * h = (1 / 2) * m * v ^ 2
have h2 : m * g * h = (1 / 2) * m * v ^ 2 := by
  sorry

-- Step 3: 2 * g * h = v ^ 2
have h3 : 2 * g * h = v ^ 2 := by
  sorry

-- Step 4: v = √(2 * g * h)
have h4 : v = Real.sqrt (2 * g * h) := by
  sorry

-- Step 5: Solve for v
have h5 : v = 10 * Real.sqrt 2 := by
  sorry

(4) Then, solve one step at a time. Each proof sketch must be a complete proof.
You MUST run lean_diagnostic_messages on the step you solve before moving on to the next steps: DO NOT MOVE ON TO THE NEXT STEP IF YOU GET ANY MESSAGE WITH SEVERITY 1. DO NOT SOLVE ALL THE STEPS AT THE SAME TIME.

You have access to the following Lean tools:

**File Operations:**
- 'lean_file_contents': Read Lean files with line numbers and annotations
- 'lean_write_file': Write content to Lean files (use this to save your proof solutions)

**Diagnostics & Analysis:**
- 'lean_diagnostic_messages': Get diagnostic messages (errors, warnings, infos) for Lean files
- 'lean_goal': Get proof goals and context at specific line positions (VERY USEFUL for understanding what to prove)
- 'lean_term_goal': Get expected type at specific location
- 'lean_hover_info': Get documentation for Lean terms, variables, functions, etc.

**Code Execution & Testing:**
- 'lean_run_code': Run complete, self-contained Lean code snippets for testing
- 'lean_multi_attempt': Test multiple code approaches at once to compare tactics

**Search Tools:**
- 'lean_leansearch': Search for theorems and lemmas using natural language queries
- 'lean_loogle': Search for definitions and theorems by type signature, name pattern, or subexpression
- 'lean_state_search': Search for theorems based on current proof state/goal
- 'lean_declaration_file': Get file contents where symbols are declared

**Code Completion:**
- 'lean_completions': Get code completions for incomplete lines/statements

WORKFLOW: lean_file_contents → lean_goal at sorry positions → work on proof → lean_write_file → lean_diagnostic_messages to verify. Use search tools when stuck or need to find relevant theorems/lemmas.

**Key Tips:**
- Always use lean_goal to understand the current proof state before making changes
- Use lean_diagnostic_messages after each edit to catch errors early
- Use search tools (lean_leansearch, lean_loogle) when you need to find relevant theorems
- Use lean_hover_info to understand Lean syntax and available functions
- Test code snippets with lean_run_code before integrating into your proof
"""

            messages = [{"role": "user", "content": prompt}]

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                tools=claude_tools,
            )

            # append assistant's output to messages
            messages.append({"role": "assistant", "content": response.content})

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

                        # Execute tool via leanclient server
                        result = await lean_client_session.call_tool(content.name, content.input)

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

            logger.info(f"✅ {name}: Task completed")

            return f"""MCPAgent Execution Result:

Agent: {name}
Model: {model}
Project: {project_path}
Iterations used: {iteration}/{max_iterations}

Final Response:
{final_response}

Tools available: {len(claude_tools)}
Lean client filter: {lean_client_filter or "None (all tools)"}"""

    except Exception as e:
        logger.error(f"❌ {name} error: {e!s}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback

        logger.error(f"❌ Full traceback: {traceback.format_exc()}")

        return f"MCPAgent error: {e!s}\n\nFull traceback:\n{traceback.format_exc()}"
