import os
import time
import pandas as pd
import pytest
from app.history import History, LoggingObserver, AutoSaveObserver
from app.calculation import Calculation
from app.calculator_config import load_config
from app.logger import get_logger

def test_history_add_undo_redo(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path))
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path))
    h = History(max_size=3)

    # add 3 calcs
    c1 = Calculation.from_values("add", 1, 2, 3)
    c2 = Calculation.from_values("add", 2, 3, 5)
    c3 = Calculation.from_values("add", 3, 4, 7)
    for c in (c1, c2, c3):
        h.add(c)

    snap3 = h.to_snapshot()
    from app.calculator_memento import Caretaker
    ct = Caretaker()
    ct.save(h.to_snapshot())

    # add one more (evicts oldest)
    c4 = Calculation.from_values("add", 4, 5, 9)
    h.add(c4)
    assert len(h.items()) == 3
    assert h.items()[0].a == 2  # first (1,2) evicted

    # undo to previous snapshot
    prev = ct.undo(h.to_snapshot())
    h.restore(prev)
    assert h.items()[0].a == 1  # restored

    # redo forward
    nxt = ct.redo(h.to_snapshot())
    h.restore(nxt)
    assert h.items()[0].a == 2  # evicted state again

def test_observers_logging_autosave(tmp_path, monkeypatch):
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path))
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path))
    monkeypatch.setenv("CALCULATOR_AUTO_SAVE", "true")

    h = History(max_size=10)
    log_ob = LoggingObserver()
    save_ob = AutoSaveObserver()

    c = Calculation.from_values("add", 1, 2, 3)
    h.add(c)
    # observers should react
    log_ob.update(c, h)
    save_ob.update(c, h)

    cfg = load_config()
    # check log file exists and history file exists
    assert os.path.exists(cfg.log_file)
    assert os.path.exists(cfg.history_file)
    df = pd.read_csv(cfg.history_file)
    assert list(df.columns) == ["operation", "a", "b", "result", "timestamp"]
    assert len(df) >= 1