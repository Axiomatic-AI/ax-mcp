from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ...providers.middleware_provider import get_mcp_middleware
from ...providers.toolset_provider import get_mcp_tools
from ...shared.utils.prompt_utils import get_feedback_prompt
from .services.pde_service import PdeService

INSTRUCTIONS = """\
This server verifies PDE solvers using the Method of Manufactured Solutions (MMS).

WORKFLOW:
1. parse_pde — turn a prose/LaTeX PDE description into a structured spec (operators,
   domain, boundary conditions, variables, unknowns). Skip this if you already have
   the operator code.
2. Choose a manufactured solution u — a smooth closed-form expression satisfying the
   boundary conditions. This is YOUR choice; no tool picks it for you.
3. derive_source — apply the operator to u to get the forcing term f = L[u] that makes
   u an exact solution.
4. verify_solution — confirm symbolically that L[u] - f == 0 and that every boundary
   condition holds. Feed f and the source terms into your solver; the solver's error
   against u should converge at the expected order.

OPERATOR SIGNATURE — every equation's `operator_code` MUST define exactly one function:

    def pde_operator(fields, vars_dict):
        # fields: dict mapping unknown names to SymPy expressions
        #   e.g. {"u": u_expr} for scalar, {"u": ..., "v": ..., "p": ...} for systems
        # vars_dict: dict mapping coordinate names to SymPy symbols
        #   e.g. {"x": x_sym, "y": y_sym, "t": t_sym}
        # Returns: a SINGLE SymPy expression L[fields] such that the PDE is L = f
        u = fields["u"]
        return sp.diff(u, vars_dict["t"]) - sp.diff(u, vars_dict["x"], 2)

Conventions:
- Use the L[u] = f convention. For u_t = u_xx + f, the operator returns u_t - u_xx.
- Use sp.diff, sp.Rational, sp.pi, sp.sin, sp.cos, sp.exp, etc. NO numpy.
- The ONLY name available besides the function arguments is `sp` (SymPy). Do NOT import anything.
- Encode numeric coefficients exactly with sp.Rational (e.g. viscosity 0.1 -> sp.Rational(1, 10)).
- Systems use one equation per row, each with its own name, e.g. "x_momentum",
  "y_momentum", "continuity" over unknowns ["u", "v", "p"].

SOLUTION AND SOURCE EXPRESSIONS are SymPy-parseable strings, keyed by field name and
equation name respectively: solution_exprs={"u": "sin(pi*x)*exp(-t)"},
source_exprs={"pde": "(-1 + pi**2)*exp(-t)*sin(pi*x)"}.

BOUNDARY CONDITION TYPES:
- Dirichlet (axis-aligned): {"label": "x=0", "type": "dirichlet", "subs": {"x": 0}, "value": "0"}
- Dirichlet (polygon edge): {"label": "edge_0", "type": "dirichlet", "subs": {"edge": [[0,0],[1,0]]}, "value": "0"}
- Neumann: {"label": "x=0", "type": "neumann", "subs": {"x": 0}, "value": "0"}
- Periodic: {"label": "periodic", "type": "periodic"}
For polygon domains, give one BC per edge using the "edge" format. Neumann uses the
OUTWARD normal, and polygon edges follow the left-normal convention (outer boundary
counter-clockwise, holes clockwise).

DOMAIN TYPES:
- interval: {"type": "interval", "x_min": 0, "x_max": 1}
- rectangle: {"type": "rectangle", "x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1}
- polygon: {"type": "polygon", "vertices": [[0,0],[1,0],[1,1],[0,1]], "edges": [[0,1],[1,2],[2,3],[3,0]]}
- disk: {"type": "disk", "center": [0, 0], "radius": 1}
For periodic domains add "periodic": true. For expression bounds use strings: "x_max": "2*pi".

The verifier is deliberately strict and fails closed: anything it cannot check (a
periodic BC with no domain, a Neumann BC whose outward normal is ambiguous, a scalar
BC value on a multi-field system) is reported as NOT passing rather than silently
accepted. A `passed: false` result is a real finding — read the residuals in
equation_diagnostics / bc_diagnostics and fix the solution, source, or BCs.
"""

mcp = FastMCP(
    name="AxPde Server",
    instructions=INSTRUCTIONS + get_feedback_prompt(["parse_pde", "derive_source", "verify_solution"]),
    version="0.0.1",
    middleware=get_mcp_middleware(),
    tools=get_mcp_tools(),
)

pde_service = PdeService()

EQUATIONS_ARG = Annotated[
    list[dict[str, Any]],
    'PDE operator(s): [{"name": "pde", "operator_code": "def pde_operator(fields, vars_dict): ..."}]. '
    "operator_code defines exactly one function returning a single SymPy expression L[fields], "
    "using the L[u] = f convention. Only `sp` (SymPy) is available; no imports, no numpy. "
    'For systems give one entry per equation, e.g. "x_momentum", "y_momentum", "continuity".',
]

SOLUTION_EXPRS_ARG = Annotated[
    dict[str, str],
    'Manufactured solution per field as SymPy-parseable strings, e.g. {"u": "sin(pi*x)*exp(-t)"}. '
    "Keys must match the field names the operator code reads from `fields`.",
]

VARIABLES_ARG = Annotated[
    list[str],
    'Coordinate names, e.g. ["x", "t"] or ["x", "y", "t"]. Supported: x, y, t, r, theta, phi.',
]


@mcp.tool(
    name="parse_pde",
    description=(
        "Parse a natural-language or LaTeX PDE description into a structured SymPy spec: "
        "the differential operator(s) as operator code, plus domain, boundary conditions, "
        "variables, and unknowns. Each operator is compile-checked before returning. "
        "The spec feeds directly into derive_source and verify_solution. "
        "This does NOT choose a manufactured solution or write a solver."
    ),
    tags=["pde", "mms", "parsing"],
)
async def parse_pde(
    description: Annotated[
        str,
        "Natural-language or LaTeX description of the PDE problem, including the equation, "
        "the domain, and the boundary conditions. "
        'E.g. "The 1D heat equation u_t = u_xx on [0,1] for t in [0,1], with homogeneous '
        'Dirichlet boundary conditions u(0,t) = u(1,t) = 0."',
    ],
) -> ToolResult:
    """Parse a PDE description into a structured SymPy spec."""
    try:
        response = pde_service.parse(description)
    except Exception as e:
        raise ToolError(f"Failed to parse PDE: {e!s}") from e

    if not response.get("success"):
        error_msg = response.get("error", "Unknown parsing error")
        return ToolResult(
            content=[TextContent(type="text", text=f"PDE parsing failed: {error_msg}")],
            structured_content=response,
        )

    spec = response.get("spec") or {}
    parts = []

    if spec.get("pde_latex"):
        parts.append(TextContent(type="text", text=f"PDE: {spec['pde_latex']}"))

    summary = [
        f"name: {spec.get('name', '(unnamed)')}",
        f"variables: {spec.get('variables', [])}",
        f"unknowns: {spec.get('unknowns', [])}",
        f"domain: {spec.get('domain', {})}",
        f"equations: {[eq.get('name') for eq in spec.get('equations', [])]}",
        f"boundary conditions: {len(spec.get('boundary_conditions', []))}",
    ]
    if spec.get("time_dependent") is not None:
        summary.append(f"time-dependent: {spec['time_dependent']}")
    parts.append(TextContent(type="text", text="\n".join(summary)))

    for eq in spec.get("equations", []):
        parts.append(TextContent(type="text", text=f"{eq.get('name')}:\n```python\n{eq.get('operator_code', '')}\n```"))

    parts.append(
        TextContent(
            type="text",
            text=("Next: choose a manufactured solution u satisfying these boundary conditions, " "then call derive_source to get the forcing term."),
        )
    )

    return ToolResult(
        content=parts,
        structured_content=response,
    )


@mcp.tool(
    name="derive_source",
    description=(
        "Derive the source term f = L[u] for a manufactured solution (deterministic, no LLM). "
        "Applies the PDE operator symbolically to the supplied solution, producing the forcing "
        "term that makes that solution exact. This is the forward step of the Method of "
        "Manufactured Solutions; pair it with verify_solution to confirm correctness."
    ),
    tags=["pde", "mms", "symbolic"],
)
async def derive_source(
    equations: EQUATIONS_ARG,
    solution_exprs: SOLUTION_EXPRS_ARG,
    variables: VARIABLES_ARG,
) -> ToolResult:
    """Derive source terms from operators and a manufactured solution."""
    try:
        response = pde_service.derive_source(equations, solution_exprs, variables)
    except Exception as e:
        raise ToolError(f"Failed to derive source: {e!s}") from e

    if not response.get("success"):
        error_msg = response.get("error", "Unknown error deriving source terms")
        return ToolResult(
            content=[TextContent(type="text", text=f"Source derivation failed: {error_msg}")],
            structured_content=response,
        )

    source_exprs = response.get("source_exprs") or {}
    lines = [f"{eq_name}: {expr}" for eq_name, expr in source_exprs.items()]
    parts = [TextContent(type="text", text="Derived source terms (f = L[u]):\n" + "\n".join(lines))]
    parts.append(
        TextContent(
            type="text",
            text="Next: call verify_solution with these source terms to confirm the residual is zero.",
        )
    )

    return ToolResult(
        content=parts,
        structured_content=response,
    )


@mcp.tool(
    name="verify_solution",
    description=(
        "Verify a manufactured solution symbolically (deterministic, no LLM). Checks that the "
        "residual L[u] - f is identically zero for each equation and that every boundary "
        "condition is satisfied. This is the hard-to-cheat verification step of the Method of "
        "Manufactured Solutions: it fails closed, so anything it cannot check is reported as "
        "not passing rather than silently accepted."
    ),
    tags=["pde", "mms", "verification"],
)
async def verify_solution(
    equations: EQUATIONS_ARG,
    solution_exprs: SOLUTION_EXPRS_ARG,
    source_exprs: Annotated[
        dict[str, str],
        'Source term per equation name as SymPy-parseable strings, e.g. {"pde": "(-1 + pi**2)*exp(-t)*sin(pi*x)"}. '
        "Keys must match the equation names. Typically these come from derive_source.",
    ],
    variables: VARIABLES_ARG,
    boundary_conditions: Annotated[
        list[dict[str, Any]] | None,
        'Boundary conditions, each {"label", "type", "subs", "value"}. Types: "dirichlet", '
        '"neumann", "periodic", "robin". Axis-aligned uses subs={"x": 0}; polygon edges use '
        'subs={"edge": [[0,0],[1,0]]}. Neumann values are with respect to the OUTWARD normal.',
    ] = None,
    domain: Annotated[
        dict[str, Any] | None,
        'Domain spec, e.g. {"type": "interval", "x_min": 0, "x_max": 1} or {"type": "rectangle", '
        '"x_min": 0, "x_max": 1, "y_min": 0, "y_max": 1}. Required for periodic and axis-aligned '
        "Neumann BCs — without it those cannot be verified and will not pass.",
    ] = None,
    unknowns: Annotated[
        list[str] | None,
        'Unknown field names, e.g. ["u"] or ["u", "v", "p"]. Defaults to ["u"].',
    ] = None,
) -> ToolResult:
    """Verify equation residuals and boundary conditions symbolically."""
    try:
        response = pde_service.verify(
            equations,
            solution_exprs,
            source_exprs,
            variables,
            boundary_conditions,
            domain,
            unknowns,
        )
    except Exception as e:
        raise ToolError(f"Failed to verify solution: {e!s}") from e

    if response.get("error"):
        return ToolResult(
            content=[TextContent(type="text", text=f"Verification error: {response['error']}")],
            structured_content=response,
        )

    passed = response.get("passed", False)
    eq_diag = response.get("equation_diagnostics") or {}
    bc_diag = response.get("bc_diagnostics") or {}

    headline = "VERIFIED: residuals are zero and all boundary conditions hold." if passed else "NOT VERIFIED"
    parts = [TextContent(type="text", text=headline)]

    if response.get("message"):
        parts.append(TextContent(type="text", text=response["message"]))

    if not passed:
        parts.append(
            TextContent(
                type="text",
                text=(
                    f"equation residuals zero: {response.get('pde_residual_zero', False)}\n"
                    f"boundary conditions satisfied: {response.get('bcs_satisfied', False)}"
                ),
            )
        )

        failing_eqs = [f"{name}: {d.get('residual')}" for name, d in eq_diag.items() if not d.get("passed")]
        if failing_eqs:
            parts.append(TextContent(type="text", text="Nonzero equation residuals:\n" + "\n".join(failing_eqs)))

        failing_bcs = [f"{label}: {d.get('residual')}" for label, d in bc_diag.items() if not d.get("passed")]
        if failing_bcs:
            parts.append(TextContent(type="text", text="Failing boundary conditions:\n" + "\n".join(failing_bcs)))

        parts.append(
            TextContent(
                type="text",
                text=(
                    "A nonzero residual means the source term does not match the operator applied to the "
                    "solution; a failing BC means the manufactured solution does not satisfy it on that "
                    "boundary. Note the verifier also reports a failure when it cannot check a condition "
                    "at all (e.g. a periodic BC with no domain given)."
                ),
            )
        )

    return ToolResult(
        content=parts,
        structured_content=response,
    )
