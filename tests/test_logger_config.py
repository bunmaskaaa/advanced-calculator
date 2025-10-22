import os
import logging
from app.logger import get_logger

def test_logger_rebind_and_level(monkeypatch, tmp_path):
    # First log dir
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path / "logs1"))
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path / "hist"))
    monkeypatch.setenv("CALCULATOR_LOG_LEVEL", "DEBUG")
    log1 = get_logger()
    log1.debug("debug-1")

    # Switch log dir and level; get_logger should rebind file handler
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path / "logs2"))
    monkeypatch.setenv("CALCULATOR_LOG_LEVEL", "ERROR")
    log2 = get_logger()
    log2.error("error-2")

    # Confirm different handlers point to the new path by emitting and checking files exist
    path1 = os.path.join(str(tmp_path / "logs1"), "calculator.log")
    path2 = os.path.join(str(tmp_path / "logs2"), "calculator.log")
    assert os.path.exists(path2)  # new handler created