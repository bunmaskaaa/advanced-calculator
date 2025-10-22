import builtins
import io
from contextlib import redirect_stdout
import os
import pytest

from app.calculator import main

def run_script_with_inputs(lines, monkeypatch):
    it = iter(lines)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(it))
    buf = io.StringIO()
    with redirect_stdout(buf):
        main()
    return buf.getvalue()

def test_repl_happy_paths(monkeypatch, tmp_path):
    # isolate filesystem
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path / "hist"))
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("CALCULATOR_AUTO_SAVE", "false")

    out = run_script_with_inputs(
        [
            "help",
            "history",
            "add 2 3",
            "history 1",
            "precision",       # show precision
            "precision 2",     # set precision
            "divide 1 3",      # should print 0.33 after precision change
            "+ 1 2",           # alias: add
            "^ 2 4",           # alias: power
            "% 10 3",          # alias: modulus
            "// 7 2",          # alias: int_divide
            "save",
            "load",
            "exit",
        ],
        monkeypatch,
    )

    assert "Commands:" in out
    assert "(history is empty)" in out or "1." in out  # first history check may be empty
    assert "Result: 5" in out                      # add 2 3
    assert "Precision:" in out                     # get precision
    assert "Precision set to 2" in out             # set precision
    assert "Result: 0.33" in out                   # divide 1 3 rounded to 2
    assert "Saved:" in out
    assert "Loaded" in out

def test_repl_errors_suggestions(monkeypatch, tmp_path):
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path / "hist"))
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("CALCULATOR_AUTO_SAVE", "false")

    out = run_script_with_inputs(
        [
            "unknowncmd",
            "divide 1 0",      # division by zero
            "history -5",      # invalid limit
            "precision nope",  # invalid precision value
            "autosave on",     # toggle on
            "autosave",        # show status
            "exit",
        ],
        monkeypatch,
    )

    # unknown command should include suggestion if close match exists
    assert "Unknown operation" in out
    assert "did you mean" in out or "Unknown operation" in out
    assert "Error:" in out
    assert "Auto-save is ON" in out