from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
from .calculation import Calculation

@dataclass(frozen=True)
class HistorySnapshot:
    state: Tuple[Calculation, ...]

class Caretaker:
    def __init__(self) -> None:
        self._undo: List[HistorySnapshot] = []
        self._redo: List[HistorySnapshot] = []

    def save(self, snapshot: HistorySnapshot) -> None:
        """Save a snapshot for potential undo and clear redo since we branched."""
        self._undo.append(snapshot)
        self._redo.clear()

    def can_undo(self) -> bool:
        return len(self._undo) > 0

    def can_redo(self) -> bool:
        return len(self._redo) > 0

    def undo(self, current: HistorySnapshot) -> HistorySnapshot:
        """Return the previous snapshot and push current to redo."""
        if not self._undo:
            raise IndexError("Nothing to undo")
        prev = self._undo.pop()
        self._redo.append(current)
        return prev

    def redo(self, current: HistorySnapshot) -> HistorySnapshot:
        """Return the next snapshot and push current back to undo."""
        if not self._redo:
            raise IndexError("Nothing to redo")
        nxt = self._redo.pop()
        self._undo.append(current)
        return nxt

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()