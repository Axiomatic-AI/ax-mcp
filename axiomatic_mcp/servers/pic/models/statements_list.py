from statements import (
    StatementType,
    StatementValidation,
    StatementValue,
    StatementValueWithValidations,
)

StatementListValue = list[StatementValueWithValidations]


class StatementList:
    def __init__(self):
        self._statements: list[StatementValue] = []
        self._validations: list[StatementValidation] = []

    @classmethod
    def create(cls) -> "StatementList":
        return cls()

    def get_statements(self) -> list[StatementValue]:
        return self._statements

    def replace_all(self, statements: list[StatementValue]) -> "StatementList":
        self._statements = statements
        return self

    def replace_at_index(self, statement: StatementValue, index: int) -> "StatementList":
        if index < 0 or index >= len(self._statements):
            raise IndexError(f"Error updating statement: Index {index} is out of bounds.")
        self._statements[index] = statement
        return self

    def delete_at_index(self, index: int) -> "StatementList":
        if index < 0 or index >= len(self._statements):
            raise IndexError(f"Error deleting statement: Index {index} is out of bounds.")
        self._statements.pop(index)
        return self

    def add(self, type_: StatementType, text: str) -> "StatementList":
        self._statements.append({"type": type_, "text": text})
        return self

    def get_count(self) -> int:
        return len(self._statements)

    def get_by_index(self, index: int) -> StatementValue:
        try:
            return self._statements[index]
        except IndexError:
            raise IndexError(f"Error getting statement: Index {index} is out of bounds.")

    def get_value(self) -> StatementListValue:
        """Combine statements with validations (if available)."""
        return [
            {
                **s,
                "validation": self._validations[i] if i < len(self._validations) else {},
            }
            for i, s in enumerate(self._statements)
        ]

    def _are_statements_equal(self, statements1: list[StatementValue], statements2: list[StatementValue]) -> bool:
        if len(statements1) != len(statements2):
            return False

        for s1, s2 in zip(statements1, statements2, strict=False):
            if not s2:
                return False
            if s1["text"] != s2["text"] or s1["type"] != s2["type"] or str(s1.get("formalization")) != str(s2.get("formalization")):
                return False
        return True

    def add_validations(self, validations: list[StatementValidation], validated_statements: list[StatementValue]) -> None:
        """Add validations only if statements match (to avoid stale updates)."""
        if not self._are_statements_equal(self._statements, validated_statements):
            return
        self._validations = validations

    def clear(self) -> None:
        self._statements = []
        self._validations = []
