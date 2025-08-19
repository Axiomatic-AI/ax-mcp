"""Autoformalizer domain MCP server."""

import os
from typing import Annotated
import httpx
from fastmcp import FastMCP

mcp = FastMCP(
    name="Statement Negation",
    instructions="""This server provides a tool for transforming Lean 4 theorems into 
their negated form. Given a Lean theorem with hypotheses and a conclusion, the tool 
returns a new theorem where the hypotheses remain unchanged, but the conclusion is 
replaced by its negation. The negation is expressed in valid Lean 4 syntax, typically 
by appending '= False' or wrapping the proposition in '¬(...)'. The proof body is left 
as 'sorry' to indicate that it has not been filled in.""",
    version="0.0.1",
)


class StatementNegationServer:
    def __init__(self):
        self.mcp = mcp
        
    def run(self):
        self.mcp.run()


@mcp.tool(
    name="negate_statement",
    description="""Takes a Lean 4 theorem and produces a negated version of its conclusion. 
The hypotheses and structure of the theorem remain unchanged, but the final proposition 
is rewritten to its logical negation. The returned output is valid Lean 4 syntax with 
the proof body replaced by 'sorry'.""",
    tags=["lean", "formalization", "mathematics"],
)
async def negate_statement(
    query: Annotated[str, "A Lean 4 theorem in valid syntax whose conclusion should be negated."],
) -> Annotated[str, "The same Lean theorem, but with the conclusion replaced by its negation and proof body set to 'sorry'."]:
    
    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required. Please set it before running.")
    
    # Prompt for OpenAI to negate the formal statement
    prompt = f"""You are given a Lean 4 theorem. Rewrite it so that its hypotheses remain 
unchanged but the conclusion is replaced by its negation. Use correct Lean 4 syntax, 
and ensure the proof body ends with ':= by sorry'. Do not add explanations.

Example input:
import Mathlib

theorem number_theory_3098 (p1 p2 p3 p4 : ℕ) (hp1 : p1.Prime) (hp2 : p2.Prime)
    (hp3 : p3.Prime) (hp4 : p4.Prime) (h1 : p1 < 100) (h2 : p2 < 100) (h3 : p3 < 100)
    (h4 : p4 < 100) (h5 : p1 ≠ p2) (h6 : p1 ≠ p3) (h7 : p1 ≠ p4) (h8 : p2 ≠ p3)
    (h9 : p2 ≠ p4) (h10 : p3 ≠ p4) (h11 : p1 = 1 ∨ p1 = 2 ∨ p1 = 3 ∨ p1 = 4 ∨ p1 = 5 ∨ p1 = 6 ∨ p1 = 7 ∨ p1 = 9)
    (h12 : p2 = 1 ∨ p2 = 2 ∨ p2 = 3 ∨ p2 = 4 ∨ p2 = 5 ∨ p2 = 6 ∨ p2 = 7 ∨ p2 = 9)
    (h13 : p3 = 1 ∨ p3 = 2 ∨ p3 = 3 ∨ p3 = 4 ∨ p3 = 5 ∨ p3 = 6 ∨ p3 = 7 ∨ p3 = 9)
    (h14 : p4 = 1 ∨ p4 = 2 ∨ p4 = 3 ∨ p4 = 4 ∨ p4 = 5 ∨ p4 = 6 ∨ p4 = 7 ∨ p4 = 9)
    (h15 : p1 ≠ p2 ∧ p1 ≠ p3 ∧ p1 ≠ p4 ∧ p2 ≠ p3 ∧ p2 ≠ p4 ∧ p3 ≠ p4) :
    (p1 + p2 + p3 + p4 = 190) := by
sorry

Example output:
import Mathlib

theorem number_theory_3098 (p1 p2 p3 p4 : ℕ) (hp1 : p1.Prime) (hp2 : p2.Prime)
    (hp3 : p3.Prime) (hp4 : p4.Prime) (h1 : p1 < 100) (h2 : p2 < 100) (h3 : p3 < 100)
    (h4 : p4 < 100) (h5 : p1 ≠ p2) (h6 : p1 ≠ p3) (h7 : p1 ≠ p4) (h8 : p2 ≠ p3)
    (h9 : p2 ≠ p4) (h10 : p3 ≠ p4) (h11 : p1 = 1 ∨ p1 = 2 ∨ p1 = 3 ∨ p1 = 4 ∨ p1 = 5 ∨ p1 = 6 ∨ p1 = 7 ∨ p1 = 9)
    (h12 : p2 = 1 ∨ p2 = 2 ∨ p2 = 3 ∨ p2 = 4 ∨ p2 = 5 ∨ p2 = 6 ∨ p2 = 7 ∨ p2 = 9)
    (h13 : p3 = 1 ∨ p3 = 2 ∨ p3 = 3 ∨ p3 = 4 ∨ p3 = 5 ∨ p3 = 6 ∨ p3 = 7 ∨ p3 = 9)
    (h14 : p4 = 1 ∨ p4 = 2 ∨ p4 = 3 ∨ p4 = 4 ∨ p4 = 5 ∨ p4 = 6 ∨ p4 = 7 ∨ p4 = 9)
    (h15 : p1 ≠ p2 ∧ p1 ≠ p3 ∧ p1 ≠ p4 ∧ p2 ≠ p3 ∧ p2 ≠ p4 ∧ p3 ≠ p4) :
    (p1 + p2 + p3 + p4 = 190) = False := by
sorry

Now negate the following theorem:

{query}
"""
    
    # Call OpenAI API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                }
            )
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid OPENAI_API_KEY. Please check your environment variable.")
            else:
                raise ValueError(f"API error: {e.response.status_code}")
        except Exception as e:
            raise ValueError(f"Failed to call OpenAI API: {str(e)}") 
