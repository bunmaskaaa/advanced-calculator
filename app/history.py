from __future__ import annotations
from typing import List, Protocol
import os
import shutil
import tempfile
import pandas as pd
from pandas.errors import EmptyDataError  # NEW

from .calculation import Calculation
from .calculator_config import load_config
from .exceptions import HistoryError
from .logger import get_logger


class Observer(Protocol):  # pragma: no cover — exercised via concrete observers
    def update(self, calc: Calculation, history: "History") -> None: ...


class History:
    def __init__(self, max_size: int) -> None:
        self._items: List[Calculation] = []
        self._max = max_size

    def items(self) -> List[Calculation]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()

    def add(self, calc: Calculation) -> None:
        self._items.append(calc)
        if len(self._items) > self._max:
            # drop oldest when exceeding capacity
            self._items.pop(0)

    def to_snapshot(self):
        from .calculator_memento import HistorySnapshot
        return HistorySnapshot(tuple(self._items))

    def restore(self, snapshot) -> None:
        self._items = list(snapshot.state)

    # --------- Persistence ----------
    def to_dataframe(self) -> pd.DataFrame:
        data = [c.to_dict() for c in self._items]
        return pd.DataFrame(data, columns=["operation", "a", "b", "result", "timestamp"])

    def _atomic_write(self, path: str, df: pd.DataFrame, encoding: str) -> None:
        """Write CSV atomically to avoid partial/corrupt files."""
        directory = os.path.dirname(path) or "."
        os.makedirs(directory, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=directory, suffix=".tmp", encoding=encoding) as tmp:
            tmp_path = tmp.name
            df.to_csv(tmp_path, index=False, encoding=encoding)
        shutil.move(tmp_path, path)

    def save_csv(self) -> str:
        cfg = load_config()
        try:
            df = self.to_dataframe()
            self._atomic_write(cfg.history_file, df, cfg.default_encoding)
            return cfg.history_file
        except Exception as e:  # pragma: no cover (pandas/internal IO)
            raise HistoryError(f"Failed to save history: {e}") from e

    def _read_with_fallback(self, path: str, primary_encoding: str) -> pd.DataFrame:
        # Try configured encoding first, then UTF-8 with BOM as a fallback
        try:
            return pd.read_csv(path, encoding=primary_encoding)
        except EmptyDataError:
            # Map empty CSV to a clear HistoryError
            raise HistoryError("History file is empty.")
        except UnicodeError:
            # Fallback for BOM or weird editors
            try:
                return pd.read_csv(path, encoding="utf-8-sig")
            except EmptyDataError:
                raise HistoryError("History file is empty.")

    def _validate_loaded_df(self, df: pd.DataFrame) -> None:
        required = {"operation", "a", "b", "result", "timestamp"}
        if df.empty:
            raise HistoryError("History file is empty.")
        if not required.issubset(df.columns):
            missing = required - set(df.columns)
            raise HistoryError(f"Malformed history file: missing columns {sorted(missing)}.")

    def load_csv(self) -> int:
        cfg = load_config()
        path = cfg.history_file
        if not os.path.exists(path):
            raise HistoryError("History file not found.")

        try:
            df = self._read_with_fallback(path, cfg.default_encoding)
            self._validate_loaded_df(df)
            df = df.astype({
                "operation": "string",
                "a": "float64",
                "b": "float64",
                "result": "float64",
                "timestamp": "string",
            }, errors="raise")
        except HistoryError:
            raise
        except ValueError as e:
            # pandas dtype conversion error
            raise HistoryError(f"Malformed history file: invalid data types ({e}).") from e
        except Exception as e:  # pragma: no cover
            raise HistoryError(f"Failed to load history: {e}") from e

        self._items = [
            Calculation(
                operation=str(row["operation"]),
                a=float(row["a"]),
                b=float(row["b"]),
                result=float(row["result"]),
                timestamp=str(row["timestamp"]),
            )
            for _, row in df.iterrows()
        ]
        return len(self._items)


# --------- Observers ----------
class LoggingObserver:
    def __init__(self) -> None:
        self._log = get_logger()

    def update(self, calc: Calculation, history: History) -> None:
        self._log.info(
            "calc=%s a=%s b=%s result=%s ts=%s size=%s",
            calc.operation, calc.a, calc.b, calc.result, calc.timestamp, len(history.items())
        )


class AutoSaveObserver:
    def __init__(self) -> None:
        self._enabled = load_config().auto_save

    def update(self, calc: Calculation, history: History) -> None:
        if self._enabled:
            history.save_csv()

    # runtime toggle API
    def set_enabled(self, value: bool) -> None:
        self._enabled = bool(value)

    def is_enabled(self) -> bool:
        return self._enabled