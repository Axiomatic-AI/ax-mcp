from typing import Literal, TypedDict


class Argument(TypedDict, total=False):
    dips: bool
    port_in: str
    port_out: str
    component: str
    wavelength_range: list[str]
    wavelengths: list[str]
    # flexible: allow arbitrary keys
    # values can be str, list[str], bool or None
    # (Python's TypedDict doesn't support index signatures cleanly,
    # but we can capture with str | list[str] | bool | None via `dict[str, Any]` at runtime)


class FormalizationEntry(TypedDict):
    arguments: Argument
    name: str


FormalizationMapping = dict[str, FormalizationEntry]


StatementType = Literal[
    "PARAMETER_CONSTRAINT",
    "COST_FUNCTION",
    "UNFORMALIZABLE_STATEMENT",
]


class Formalization(TypedDict):
    code: str
    mapping: FormalizationMapping
    default_tolerance: float


class StatementValue(TypedDict, total=False):
    type: StatementType
    text: str
    formalization: Formalization
    isFormalizing: bool
    isInformalizing: bool
    hasFormalizationError: bool
    hasInformalizationError: bool


class StatementValidation(TypedDict, total=False):
    holds: bool
    satisfiable: bool
    message: str
    isDirty: bool


class StatementValueWithValidations(StatementValue, total=False):
    validation: StatementValidation
