from fastmcp import FastMCP
from fastmcp.tools.tool import ToolResult
from ...shared import AxiomaticAPIClient

mcp = FastMCP(
    name="Axiomatic Equations Server",
    instructions="""This server provides tools to compose and analyze equations.""",
    version="0.0.1",
)

@mcp.tool(
    name="compose_expression",
    description="Compose an expression for a given task",
    tags=["equations", "compose"],
)

async def compose_expression( source_document: str, task: str) -> ToolResult:
    
    input_body = {
        "source_document": source_document,
        "task": task,
    }

    response = AxiomaticAPIClient().post("/document/expression/compose", input_body=input_body)

    return ToolResult(
        composed_expression = response["composed_expression"],
        comments = response["comments"],
        composition_code = response["composition_code"]
    )



if __name__ == "__main__":
    import os
    import sys

    # Add the project root to the Python path when running directly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    sys.path.insert(0, project_root)

    from api.src.models.expr_compostion import (
        CompositionOutputBody,  # Re-import for direct script execution
    )

    source_doc = """# Ways of Describing Kinetic Energy

    Kinetic energy is the energy associated with the motion of an object. It can be described in several complementary ways depending on the context (mechanics, relativity, quantum physics, or thermodynamics).

    ---

    ## 1. Classical Mechanics (Newtonian Definition)

    - **Formula**:  
    \\[
    KE = \frac{1}{2}mv^2
    \\]  
    where:
    - \\(m\\) = mass of the object  
    - \\(v\\) = velocity of the object  

    - **Interpretation**:  
    It is the work required to accelerate an object of mass \\(m\\) from rest to velocity \\(v\\). If the velocity doubles, the kinetic energy quadruples.

    ---

    ## 2. Work–Energy Principle

    - **Statement**: The net work done on an object by all external forces is equal to the change in its kinetic energy.  
    \\[
    W_{net} = \\Delta KE
    \\]

    - **Interpretation**: Kinetic energy is a bookkeeping tool for understanding how forces transfer energy to moving objects.

    ---

    ## 3. Momentum-Based Expression

    - Using momentum \\(p = mv\\):  
    \\[
    KE = \frac{p^2}{2m}
    \\]

    - **Why useful**: This form is convenient when momentum is conserved (e.g., in collisions) and when velocity is not directly known.

    ---

    ## 4. Relativistic Kinetic Energy

    - In Einstein’s special relativity, kinetic energy accounts for effects at speeds close to the speed of light:  
    \\[
    KE = (\\gamma - 1)mc^2
    \\]  
    where  
    \\(\\gamma = \frac{1}{\\sqrt{1 - \frac{v^2}{c^2}}}\\)

    - **Interpretation**: As \\(v \to c\\), the kinetic energy grows without bound, which is why no object with mass can reach the speed of light.

    ---

    ## 5. Microscopic / Thermal View

    - In thermodynamics, the **kinetic energy of particles** (atoms, molecules) is linked to **temperature**:  
    \\[
    \\langle KE \rangle = \frac{3}{2}k_B T
    \\]  
    for a monatomic ideal gas.  

    - **Interpretation**: Temperature is a measure of the average kinetic energy of particles in a substance.

    ---

    ## 6. Quantum Mechanical Perspective

    - In quantum mechanics, kinetic energy is represented as an **operator**:  
    \\[
    \\hat{T} = -\frac{\\hbar^2}{2m} \nabla^2
    \\]

    - **Interpretation**: This operator acts on a particle’s wavefunction to calculate its kinetic energy contribution in the Schrödinger equation.

    ---

    ## 7. Geometric / Energy of Motion Description

    - Kinetic energy can also be thought of as **energy due to change of position over time** in generalized coordinates (Lagrangian mechanics).  
    - In this view:  
    \\[
    L = T - V
    \\]  
    where \\(T\\) is kinetic energy and \\(V\\) is potential energy.

    """

    task = "derive the expression for kinetic energy as a function of mass and velocity"

    service = ExpressionComposition()
    output = service.compose_expression(source_doc, task)
    print(output)
