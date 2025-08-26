from typing import Optional

from ...constants.api_constants import ApiRoutes
from ..models.statements import (
    StatementValue,
    StatementValueWithValidations,
)
from ..models.statements_list import StatementListValue
from ..utils.physics import get_linear_range, str_units_to_um
from .axiomatic_api_client import AxiomaticApiClient


class StatementsService:
    _instance: Optional["StatementsService"] = None

    def __init__(self):
        self.api_client = AxiomaticApiClient.get_instance()

    @classmethod
    def get_instance(cls) -> "StatementsService":
        if cls._instance is None:
            cls._instance = StatementsService()
        return cls._instance

    async def formalize_query(
        self,
        query: str,
        statements: list[StatementValueWithValidations],
        pdk_type: str,
    ) -> StatementListValue | None:
        # remove validation before sending
        statements_without_validation = [{k: v for k, v in s.items() if k != "validation"} for s in statements]

        response = await self.api_client.post(
            ApiRoutes.FORMALIZE_CIRCUIT,
            {"query": query, "statements": statements_without_validation},
        )

        if not response or "statements" not in response:
            raise ValueError("No formalized statements returned")

        return response["statements"]

    def extract_wavelengths_from_statements(self, statements: list[StatementValue]) -> list[float] | None:
        w = self._get_wavelengths(statements)
        r = self._get_wavelength_range(statements)

        min_val = min(w["min"], r["min"])
        max_val = max(w["max"], r["max"])

        if float("inf") not in (min_val, max_val) and max_val != min_val:
            return self._get_range_for_multiple_wavelengths(min_val, max_val)
        elif float("inf") not in (min_val, max_val) and w["min"] == w["max"]:
            return self._get_range_for_single_wavelength(w["min"])
        else:
            return None

    def _get_wavelengths(self, statements: list[StatementValue]) -> dict:
        wavelengths: list[float] = []
        for s in statements:
            mapping = s.get("formalization", {}).get("mapping", {})
            for m in mapping.values():
                args = m.get("arguments", {})
                if args.get("wavelengths"):
                    for w in args["wavelengths"]:
                        val = str_units_to_um(w)
                        if not (val is None or val != val):  # filter NaN
                            wavelengths.append(val)

        return {
            "min": min(wavelengths) if wavelengths else float("inf"),
            "max": max(wavelengths) if wavelengths else float("-inf"),
        }

    def _get_wavelength_range(self, statements: list[StatementValue]) -> dict:
        ranges: list[tuple[float, float]] = []
        for s in statements:
            mapping = s.get("formalization", {}).get("mapping", {})
            for m in mapping.values():
                args = m.get("arguments", {})
                if args.get("wavelength_range"):
                    min_str, max_str = args["wavelength_range"]
                    min_val, max_val = str_units_to_um(min_str), str_units_to_um(max_str)
                    if not (min_val != min_val or max_val != max_val):  # filter NaN
                        ranges.append((min_val, max_val))

        result = {"min": float("inf"), "max": float("-inf")}
        for min_val, max_val in ranges:
            result["min"] = min(result["min"], min_val)
            result["max"] = max(result["max"], max_val)

        return result

    def _get_range_for_multiple_wavelengths(self, min_val: float, max_val: float, num_points: int = 10000) -> list[float]:
        return get_linear_range(min=min_val, max=max_val, num_points=num_points)

    def _get_range_for_single_wavelength(self, value: float, num_points: int = 10000) -> list[float]:
        delta = value * 0.1
        return get_linear_range(min=value - delta, max=value + delta, num_points=num_points)

    async def formalize_statement(self, statement: StatementValue) -> StatementValue:
        response = await self.api_client.post(
            ApiRoutes.FORMALIZE_STATEMENT,
            {"query": "", "statements": [statement]},
        )

        if not response or "statements" not in response:
            raise ValueError("No formalized statements returned")

        stmts = response["statements"]
        if len(stmts) == 1:
            return stmts[0]
        elif len(stmts) == 2:
            return stmts[1]
        else:
            raise ValueError("Invalid formalized statements length")

    async def informalize_statement(self, statement: StatementValue) -> str:
        response = await self.api_client.post(
            ApiRoutes.INFORMALIZE_STATEMENT,
            {"query": "", "statement": statement},
        )

        if not response or "text" not in response:
            raise ValueError("No formalized statement text returned")

        return response["text"]
