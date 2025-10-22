import os
import pandas as pd
import pytest
from app.history import History
from app.exceptions import HistoryError

def test_load_missing_file(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path))
    h = History(max_size=10)
    with pytest.raises(HistoryError, match="not found"):
        h.load_csv()

def test_load_empty_file(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path))
    path = tmp_path / "history.csv"
    path.write_text("", encoding="utf-8")
    h = History(max_size=10)
    with pytest.raises(HistoryError, match="empty"):
        h.load_csv()

def test_load_malformed_missing_columns(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path))
    # Write CSV missing the 'timestamp' and 'result' columns
    df = pd.DataFrame({"operation": ["add"], "a": [1.0], "b": [2.0]})
    path = tmp_path / "history.csv"
    df.to_csv(path, index=False, encoding="utf-8")
    h = History(max_size=10)
    with pytest.raises(HistoryError, match="missing columns"):
        h.load_csv()

def test_load_bad_types(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path))
    # result cannot be cast to float
    df = pd.DataFrame({
        "operation": ["add"],
        "a": [1.0],
        "b": [2.0],
        "result": ["not-a-float"],
        "timestamp": ["2025-01-01T00:00:00+00:00"],
    })
    path = tmp_path / "history.csv"
    df.to_csv(path, index=False, encoding="utf-8")
    h = History(max_size=10)
    with pytest.raises(HistoryError, match="invalid data types"):
        h.load_csv()

def test_atomic_save(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path))
    h = History(max_size=10)
    # Save with empty history still writes a well-formed file (0 rows)
    out = h.save_csv()
    assert os.path.exists(out)
    # File should be readable (just empty or with header)
    df = pd.read_csv(out)
    assert list(df.columns) == ["operation", "a", "b", "result", "timestamp"]