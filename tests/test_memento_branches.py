import pytest
from app.calculator_memento import Caretaker
from app.history import History
from app.calculation import Calculation

def test_memento_empty_undo_redo_errors():
    ct = Caretaker()
    h = History(5)
    snap = h.to_snapshot()
    with pytest.raises(IndexError):
        ct.undo(snap)
    with pytest.raises(IndexError):
        ct.redo(snap)