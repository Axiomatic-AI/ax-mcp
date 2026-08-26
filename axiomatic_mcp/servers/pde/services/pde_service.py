"""Service for PDE / Method-of-Manufactured-Solutions API calls."""

from typing import Any

from ....shared import AxiomaticAPIClient
from ....shared.constants.api_constants import ApiRoutes
from ....shared.models.singleton_base import SingletonBase


class PdeService(SingletonBase):
    """Thin proxy service for the PDE parse / derive-source / verify endpoints."""

    def parse(self, description: str) -> dict[str, Any]:
        """
        Parse a natural-language or LaTeX PDE description into a structured SymPy spec.

        Args:
            description: Natural language or LaTeX description of the PDE problem.

        Returns:
            dict with keys: success, spec, compile_results, error
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.PDE_PARSE,
                data={"description": description},
            )

    def derive_source(
        self,
        equations: list[dict[str, Any]],
        solution_exprs: dict[str, str],
        variables: list[str],
    ) -> dict[str, Any]:
        """
        Derive the source term f = L[u] for a manufactured solution.

        Args:
            equations: [{"name": ..., "operator_code": ...}] PDE operator(s).
            solution_exprs: Manufactured solution per field, e.g. {"u": "sin(pi*x)*exp(-t)"}.
            variables: Coordinate names, e.g. ["x", "t"].

        Returns:
            dict with keys: success, source_exprs, error
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.PDE_DERIVE_SOURCE,
                data={
                    "equations": equations,
                    "solution_exprs": solution_exprs,
                    "variables": variables,
                },
            )

    def verify(
        self,
        equations: list[dict[str, Any]],
        solution_exprs: dict[str, str],
        source_exprs: dict[str, str],
        variables: list[str],
        boundary_conditions: list[dict[str, Any]] | None = None,
        domain: dict[str, Any] | None = None,
        unknowns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Verify that L[u] - f == 0 for each equation and that all BCs hold.

        Args:
            equations: [{"name": ..., "operator_code": ...}] PDE operator(s).
            solution_exprs: Manufactured solution per field.
            source_exprs: Source term per equation name.
            variables: Coordinate names.
            boundary_conditions: BC specs, each {"label", "type", "subs", "value"}.
            domain: Domain spec, e.g. {"type": "interval", "x_min": 0, "x_max": 1}.
            unknowns: Unknown field names, defaults to ["u"].

        Returns:
            dict with keys: passed, pde_residual_zero, bcs_satisfied,
            equation_diagnostics, bc_diagnostics, message, error
        """
        with AxiomaticAPIClient() as client:
            return client.post(
                ApiRoutes.PDE_VERIFY,
                data={
                    "equations": equations,
                    "solution_exprs": solution_exprs,
                    "source_exprs": source_exprs,
                    "variables": variables,
                    "boundary_conditions": boundary_conditions or [],
                    "domain": domain or {},
                    "unknowns": unknowns or ["u"],
                },
            )
