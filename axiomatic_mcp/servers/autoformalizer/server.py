"""Autoformalizer domain MCP server."""

import os
from typing import Annotated
import httpx
from fastmcp import FastMCP

mcp = FastMCP(
    name="Autoformalizer",
    instructions="""This server provides tools to convert natural language mathematical 
    statements into formal Lean theorem statements with sorry placeholders.""",
    version="0.0.1",
)


class AutoformalizerServer:
    def __init__(self):
        self.mcp = mcp
        
    def run(self):
        self.mcp.run()


@mcp.tool(
    name="formalize_statement",
    description="Convert natural language mathematical statement to Lean theorem with sorry",
    tags=["lean", "formalization", "mathematics"],
)
async def formalize_statement(
    query: Annotated[str, "Natural language mathematical statement to formalize"],
) -> Annotated[str, "Lean theorem statement with sorry placeholder"]:
    """Convert natural language mathematical statement to Lean theorem."""
    
    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Prompt for OpenAI to formalize the statement
    prompt = f"""Convert the following natural language mathematical statement into a Lean 4 theorem statement with a sorry placeholder.

Natural language statement: {query}

Please provide ONLY the Lean theorem statement in the following format:
- Use proper Lean 4 syntax
- Include appropriate theorem name (use snake_case)
- Include necessary hypotheses as parameters
- End with := by sorry
- Do not include any explanations or additional text

Example input: "If every prime greater than 2 is odd, then 7 must be odd. Is this true?"
Example output: theorem seven_is_odd (h : ∀ p : ℕ, p > 2 ∧ Nat.Prime p → Odd p) : Odd 7 := by sorry

Your response:"""
    
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
                raise ValueError("Invalid OPENAI_API_KEY")
            else:
                raise ValueError(f"API error: {e.response.status_code}")
        except Exception as e:
            raise ValueError(f"Failed to call OpenAI API: {str(e)}")