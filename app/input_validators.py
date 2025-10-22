from __future__ import annotations
from .exceptions import ValidationError
from .calculator_config import load_config

def parse_two_numbers(tokens: list[str]) -> tuple[float, float]:
    if len(tokens) != 2:
        raise ValidationError("Exactly two operands required.")
    try:
        a = float(tokens[0]); b = float(tokens[1])
    except ValueError as e:
        raise ValidationError("Operands must be numeric.") from e

    cfg = load_config()
    for v in (a, b):
        if abs(v) > cfg.max_input_value:
            raise ValidationError("Operand exceeds maximum allowed value.")
    return a, b