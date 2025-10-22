import math
import pytest
from app.input_validators import parse_two_numbers
from app.exceptions import ValidationError
from app.calculator_config import load_config

def test_requires_exactly_two_numbers():
    with pytest.raises(ValidationError):
        parse_two_numbers([])

    with pytest.raises(ValidationError):
        parse_two_numbers(["1"])

    with pytest.raises(ValidationError):
        parse_two_numbers(["1", "2", "3"])


@pytest.mark.parametrize("a,b", [
    ("x", "2"),
    ("1.2", "y"),
    ("hello", "world"),
])
def test_non_numeric_inputs(a, b):
    with pytest.raises(ValidationError):
        parse_two_numbers([a, b])


def test_within_max_range_passes(monkeypatch):
    # Set a small max to make test deterministic
    monkeypatch.setenv("CALCULATOR_MAX_INPUT_VALUE", "1000")
    a, b = parse_two_numbers(["999.9", "-1000"])
    assert a == 999.9
    assert b == -1000.0


@pytest.mark.parametrize("val", ["1000.1", "1e6", "-1e9"])
def test_exceeds_max_input_raises(monkeypatch, val):
    monkeypatch.setenv("CALCULATOR_MAX_INPUT_VALUE", "1000")
    with pytest.raises(ValidationError):
        parse_two_numbers([val, "1"])


def test_boundary_values(monkeypatch):
    # exactly at the limit should be OK
    monkeypatch.setenv("CALCULATOR_MAX_INPUT_VALUE", "42")
    a, b = parse_two_numbers(["42", "-42"])
    assert a == 42.0 and b == -42.0