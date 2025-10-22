from app.calculator import Calculator

def test_precision_runtime_change(monkeypatch, tmp_path):
    # isolate I/O dirs
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path / "hist"))
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path / "logs"))

    c = Calculator()
    # default precision from .env (6) unless changed
    r1 = c.calculate("divide", 1, 3)
    # now change precision to 2 and compute again
    c.cmd_set_precision(2)
    r2 = c.calculate("divide", 1, 3)
    assert r1 != r2           # rounding should differ
    assert r2 == 0.33         # 1/3 rounded to 2 decimals