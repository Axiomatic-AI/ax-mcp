import asyncio
from typing import Annotated

from fastmcp import FastMCP

from ...shared import AxiomaticAPIClient

mcp = FastMCP(
    name="Autoformalizer",
    instructions="""You are an expert Lean 4 theorem formalizer. Convert natural language mathematical statements into syntactically correct Lean 4 theorem declarations.

FORMALIZATION RULES:
- Use descriptive snake_case theorem names
- Include necessary hypotheses as parameters
- Use proper Lean 4 and Mathlib syntax
- End all theorems with := by sorry
- Follow current Mathlib naming conventions
- Include necessary imports at the top (e.g., import Mathlib.Data.Nat.Prime.Basic)
- CRITICAL: Never use escaped quotes (\") in comments - use simple quotes or rephrase without quotes

EXAMPLES:
Input: "All prime numbers greater than 2 are odd"
Output:

-- code block --
import Mathlib.Data.Nat.Prime.Basic
import Mathlib.Data.Nat.Parity.Basic

theorem primes_gt_two_odd : ∀ p : ℕ, p > 2 ∧ Nat.Prime p → Odd p := by sorry


Input: "The square root of 2 is irrational"
Output: 

-- code block --
import Mathlib.Data.Real.Irrational
import Mathlib.Data.Real.Sqrt

theorem sqrt_two_irrational : Irrational (Real.sqrt 2) := by sorry

Once complete, execute the code to ensure there are no syntactical errors. You may do several attempts in parallel with the execute_list tool.

Return all completed code blocks, including the import statements and the theorem declaration.""",
    version="0.0.1",
)


def _execute_lean_code(code: str) -> str:
    """Core execution logic for Lean code."""
    data = {"code": code}
    response = AxiomaticAPIClient().post("/lean/execute", data=data)
    return f"{response['status']}\n{response['stdout']}"


@mcp.tool(
    name="execute_lean_code",
    description='Execute Lean 4 code and return compilation results. IMPORTANT: Do not use escaped quotes (") in comments',
    tags=["lean", "execution", "validation"],
)
async def execute_lean_code(
    code: Annotated[str, "Lean 4 code to execute"],
) -> Annotated[str, "Execution results"]:
    """Execute Lean code via Axiomatic API."""
    return await asyncio.to_thread(_execute_lean_code, code)


@mcp.tool(
    name="execute_list",
    description='Execute a list of Lean 4 code snippets in parallel. IMPORTANT: Do not use escaped quotes (") in comments',
    tags=["lean", "execution", "parallel"],
)
async def execute_list(
    codes: Annotated[list[str], "List of Lean 4 code snippets to execute"],
) -> Annotated[list[str], "List of execution results"]:
    """Execute multiple Lean code snippets concurrently."""
    tasks = [asyncio.to_thread(_execute_lean_code, code) for code in codes]
    return await asyncio.gather(*tasks)


# @mcp.tool(
#     name="write_lean_file",
#     description="Write Lean code to a file",
#     tags=["lean", "file"],
# )


# async def write_lean_file(
#     lean_code: Annotated[str, "Lean code to write"],
# ) -> Annotated[str, "Result"]:
#     """Write Lean code to a file."""

#     try:
#         path = Path(file_path)
#         with open(path, "w") as f:
#             f.write(lean_code)
#         return f"✅ Wrote {file_path}"
#     except Exception as e:
#         return f"❌ Error: {e}"
