"""MCP server that exposes the exact MCPAgent as a tool."""

import logging
import os
from typing import List, Optional, Annotated

import anthropic
from fastmcp import FastMCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

mcp = FastMCP(
    name="Lean Prover",
    instructions="A prover that uses the exact MCPAgent implementation as a tool.",
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
        if hasattr(content, 'text'):
            text_parts.append(content.text)
        elif content.type == 'tool_use':
            tool_parts.append(content.name)

    claude_message = " ".join(text_parts)
    if tool_parts:
        claude_message += f" I will use tools: {', '.join(tool_parts)}"

    return claude_message

@mcp.tool(
    name="mcp_agent_execute",
    description="Execute MCPAgent with Lean tools only on Lean code",
    tags=["lean", "proving", "mcp", "agent"],
)
async def mcp_agent_execute(
    lean_code: Annotated[str, "Lean code to analyze and prove"],
    project_path: Annotated[str, "Path to the Lean project"] = "/Users/marcodeltredici/PycharmProjects/Axiomatic/AX_Lean_Physics",
    name: Annotated[str, "Agent name"] = "Prover",
    model: Annotated[str, "Claude model to use"] = "claude-sonnet-4-20250514",
    lean_tools_filter: Annotated[Optional[List[str]], "List of Lean tools to include (None = all tools)"] = None,
    max_iterations: Annotated[int, "Maximum tool use iterations"] = 100,
    max_tokens: Annotated[int, "Maximum tokens per API call"] = 5000,
) -> Annotated[str, "Agent execution result"]:
    """Execute MCPAgent with Lean tools to prove theorems in Lean code."""
    
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
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/tmp/mcp_agent_debug.log', mode='w'),  # 'w' mode overwrites the file
                logging.StreamHandler()
            ]
        )
    
    # Agent configuration (matching the original)
    lean_lsp_path = "/Users/marcodeltredici/PycharmProjects/Axiomatic/lean-lsp-mcp"
    
    logger.info(f"🔧 {name}: Start task")

    env = os.environ.copy()
    env["LEAN_PROJECT_PATH"] = project_path
    
    # Add elan bin directory to PATH so lake command can be found
    current_path = env.get("PATH", "")
    elan_path = "/Users/marcodeltredici/.elan/bin"
    if elan_path not in current_path:
        env["PATH"] = f"{elan_path}:{current_path}"

    # Initialize Lean MCP server
    lean_params = StdioServerParameters(
        command=f"{lean_lsp_path}/.venv/bin/python",
        args=["-m", "lean_lsp_mcp", "--transport", "stdio"],
        cwd=lean_lsp_path,
        env=env,
    )

    try:
        # Connect to lean server only
        async with stdio_client(lean_params) as (lean_read, lean_write):

            async with ClientSession(lean_read, lean_write) as lean_session:
                # Initialize lean session
                await lean_session.initialize()

                # Get tools from lean server
                lean_tools = await lean_session.list_tools()

                logger.info(f"🔧 Lean tools: {[tool.name for tool in lean_tools.tools]}")

                client = anthropic.Anthropic(api_key=api_key)

                # Convert lean MCP tools to Claude format
                claude_tools = []

                # Add lean tools (filtered if specified)
                for tool in lean_tools.tools:
                    if (
                        lean_tools_filter is None
                        or tool.name in lean_tools_filter
                    ):
                        claude_tools.append(
                            {
                                "name": tool.name,
                                "description": f"[Lean] {tool.description}",
                                "input_schema": tool.inputSchema,
                            }
                        )

                logger.info(f"✅ Total tools available to Claude: {len(claude_tools)}")

                # Create initial message with lean code
                prompt = f"""You are an expert Lean theorem prover. Here is the Lean code:

```lean
{lean_code}
```

IMPORTANT: Before doing anything else, you MUST first run lean_diagnostic_messages on this code to check for any existing errors.

The general approach you must follow is:
(1) Run lean_diagnostic_messages on the Lean code to analyze the current state
(2) look at the theorem and identify proofs with a 'sorry'. 
(3) You then MUST Produce a initial sketch of the proof: this must be a high-level outline of the proof steps without any specific tactics or code.
(3) You then MUST Formalize each step of the proof in Lean4 using have statements but YOU CANNOT include any tactics. For example, given this input

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

You can use the following Lean tools:
    - 'lean_diagnostic_messages': Get diagnostic messages (errors, warnings)
    - 'lean_goal': Get the current proof goal at a position
    - 'lean_hover_info': Get hover information for symbols
    - 'lean_multi_attempt': Try multiple proof attempts
    - 'lean_leansearch': Search for theorems and lemmas
    - 'lean_loogle': Search for lemmas by type signature

It is VERY IMPORTANT that you use lean tools, especially those for searching, when you create your proofs, especially if you get stuck. 
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

                while (
                    response.stop_reason == "tool_use"
                    and iteration < max_iterations
                ):
                    iteration += 1
                    logger.info(f"🔄 {name} iteration {iteration}")

                    tool_results = []
                    for content in response.content:
                        if content.type == "tool_use":
                            logger.info(f"🔧 Using tool: {content.name}")
                            logger.info(f"📥 Input: {content.input}")

                            # Execute tool via lean server
                            result = await lean_session.call_tool(
                                content.name, content.input
                            )

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

                    messages.append(
                        {"role": "assistant", "content": response.content}
                    )

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
Lean tools filter: {lean_tools_filter or 'None (all tools)'}"""

    except Exception as e:
        logger.error(f"❌ {name} error: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        
        return f"MCPAgent error: {str(e)}\n\nFull traceback:\n{traceback.format_exc()}"