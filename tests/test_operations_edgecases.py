import pytest
from app.operations import OperationFactory
from app.exceptions import OperationError

def test_root_negative_non_integer_index():
    with pytest.raises(OperationError, match="requires an integer index"):
        OperationFactory.create("root").execute(-16, 2.5)