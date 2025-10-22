from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone  # compatible across Python 3.10–3.13
from typing import Dict, Any


@dataclass
class Calculation:
    """Represents a single calculator operation and its result."""
    operation: str
    a: float
    b: float
    result: float
    timestamp: str

    @classmethod
    def from_values(cls, operation: str, a: float, b: float, result: float) -> "Calculation":
        """Factory method to create a Calculation with an auto-generated UTC timestamp."""
        return cls(
            operation=operation,
            a=a,
            b=b,
            result=result,
            timestamp=datetime.now(timezone.utc).isoformat()  # universal UTC timestamp
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert this Calculation to a serializable dictionary."""
        return asdict(self)