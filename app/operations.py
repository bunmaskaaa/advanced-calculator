from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from .exceptions import OperationError

class BinaryOperation(Protocol):
    def execute(self, a: float, b: float) -> float: ...  # pragma: no cover


@dataclass
class Add:
    def execute(self, a: float, b: float) -> float:
        return a + b


@dataclass
class Subtract:
    def execute(self, a: float, b: float) -> float:
        return a - b


@dataclass
class Multiply:
    def execute(self, a: float, b: float) -> float:
        return a * b


@dataclass
class Divide:
    def execute(self, a: float, b: float) -> float:
        if b == 0:
            raise OperationError("Division by zero.")
        return a / b


@dataclass
class Power:
    def execute(self, a: float, b: float) -> float:
        return a ** b


@dataclass
class Root:
    def execute(self, a: float, b: float) -> float:
        if b == 0:
            raise OperationError("Zeroth root undefined.")

        # Negative base handling: only allowed for odd *integer* indices.
        if a < 0:
            # b must be an integer (within float representation)
            if float(b).is_integer():
                n = int(b)
                if n % 2 == 0:
                    raise OperationError("Even root of negative number is not real.")
                # odd integer root of a negative number is negative real:
                return - (abs(a) ** (1.0 / n))
            else:
                raise OperationError("Root of negative base requires an integer index.")

        # Non-negative base: standard real root
        return a ** (1.0 / b)


@dataclass
class Modulus:
    def execute(self, a: float, b: float) -> float:
        if b == 0:
            raise OperationError("Modulus by zero.")
        return a % b


@dataclass
class IntDivide:
    def execute(self, a: float, b: float) -> float:
        if b == 0:
            raise OperationError("Integer division by zero.")
        return a // b


@dataclass
class Percent:
    def execute(self, a: float, b: float) -> float:
        if b == 0:
            raise OperationError("Percentage with denominator zero.")
        return (a / b) * 100.0


@dataclass
class AbsDiff:
    def execute(self, a: float, b: float) -> float:
        return abs(a - b)


class OperationFactory:
    mapping = {
        "add": Add,
        "subtract": Subtract,
        "multiply": Multiply,
        "divide": Divide,
        "power": Power,
        "root": Root,
        "modulus": Modulus,
        "int_divide": IntDivide,
        "percent": Percent,
        "abs_diff": AbsDiff,
    }

    @classmethod
    def create(cls, name: str) -> BinaryOperation:
        key = name.strip().lower()
        try:
            return cls.mapping[key]()
        except KeyError as e:
            raise OperationError(f"Unknown operation: {name}") from e