from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from typing import Dict, Any

@dataclass
class Calculation:
    """
    Immutable record of a single calculation.
    - operation: the operation name (e.g., 'add', 'power', 'root', etc.)
    - a, b: numeric operands used for the operation
    - result: numeric result (already precision-rounded by Calculator)
    - timestamp: ISO 8601 UTC timestamp when the calc was performed
    """
    operation: str
    a: float
    b: float
    result: float
    timestamp: str

    @classmethod
    def from_values(cls, operation: str, a: float, b: float, result: float) -> "Calculation":
        """
        Factory that attaches a timezone-aware UTC timestamp to the record.
        """
        return cls(
            operation=operation,
            a=a,
            b=b,
            result=result,
            timestamp=datetime.now(UTC).isoformat()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dict for pandas/csv serialization."""
        return asdict(self)