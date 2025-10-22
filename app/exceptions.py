class CalculatorError(Exception):
    """Base exception for calculator."""


class OperationError(CalculatorError):
    """Invalid or failed operation."""


class ValidationError(CalculatorError):
    """Input validation failure."""


class HistoryError(CalculatorError):
    """History / undo-redo related failure."""