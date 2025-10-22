import pytest
from app.operations import OperationFactory
from app.exceptions import OperationError

@pytest.mark.parametrize("op,a,b,exp", [
    ("add", 2, 3, 5),
    ("subtract", 5, 2, 3),
    ("multiply", 3, 4, 12),
    ("divide", 9, 3, 3),
    ("power", 2, 5, 32),
    ("modulus", 10, 4, 2),
    ("int_divide", 10, 3, 3),
    ("percent", 25, 100, 25.0),
    ("abs_diff", 5, 11, 6),
])
def test_basic_ops(op, a, b, exp):
    result = OperationFactory.create(op).execute(a, b)
    assert result == exp

def test_divide_by_zero():
    with pytest.raises(OperationError):
        OperationFactory.create("divide").execute(1, 0)

def test_mod_by_zero():
    with pytest.raises(OperationError):
        OperationFactory.create("modulus").execute(1, 0)

def test_int_divide_by_zero():
    with pytest.raises(OperationError):
        OperationFactory.create("int_divide").execute(1, 0)

def test_root_even_negative():
    with pytest.raises(OperationError):
        OperationFactory.create("root").execute(-8, 2)

def test_root_ok_odd():
    result = OperationFactory.create("root").execute(-27, 3)
    assert pytest.approx(result, rel=1e-9) == -3

def test_unknown_operation():
    with pytest.raises(OperationError):
        OperationFactory.create("unknown-op")