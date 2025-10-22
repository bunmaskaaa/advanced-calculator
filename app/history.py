from __future__ import annotations
from typing import List, Protocol
import pandas as pd
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

    def save_csv(self) -> str:
        cfg = load_config()
        try:
            df = self.to_dataframe()
            df.to_csv(cfg.history_file, index=False, encoding=cfg.default_encoding)
            return cfg.history_file
        except Exception as e:  # pragma: no cover (pandas internals)
            raise HistoryError(f"Failed to save history: {e}") from e

    def load_csv(self) -> int:
        cfg = load_config()
        try:
            df = pd.read_csv(cfg.history_file, encoding=cfg.default_encoding)
        except FileNotFoundError:
            raise HistoryError("History file not found.")
        except Exception as e:  # pragma: no cover
            raise HistoryError(f"Failed to load history: {e}") from e

        required = {"operation", "a", "b", "result", "timestamp"}
        if not required.issubset(df.columns):
            raise HistoryError("Malformed history file.")

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

    # --- NEW: runtime toggle API ---
    def set_enabled(self, value: bool) -> None:
        self._enabled = bool(value)

    def is_enabled(self) -> bool:
        return self._enabled