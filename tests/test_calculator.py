import os
import pytest
from app.calculator import Calculator
from app.exceptions import OperationError, ValidationError

def test_calculate_and_history(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path / "hist"))
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("CALCULATOR_AUTO_SAVE", "false")  # disable autosave for this test

    calc = Calculator()
    r = calc.calculate("add", 2, 3)
    assert r == 5
    assert len(calc.cmd_history()) == 1

    # undo/redo
    calc.cmd_undo()
    assert len(calc.cmd_history()) == 0
    calc.cmd_redo()
    assert len(calc.cmd_history()) == 1

def test_unknown_op_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path))
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path))
    c = Calculator()
    with pytest.raises(OperationError):
        c.calculate("does_not_exist", 1, 2)

def test_save_load(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path / "hist"))
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path / "logs"))

    c = Calculator()
    c.calculate("multiply", 3, 4)
    path = c.cmd_save()
    assert os.path.exists(path)
    c.cmd_clear()
    assert len(c.cmd_history()) == 0
    n = c.cmd_load()
    assert n == 1
    assert len(c.cmd_history()) == 1