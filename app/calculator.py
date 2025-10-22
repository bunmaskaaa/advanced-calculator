from __future__ import annotations
from typing import List, Dict
from colorama import init as color_init, Fore
import difflib

from .operations import OperationFactory
from .input_validators import parse_two_numbers
from .calculation import Calculation
from .exceptions import CalculatorError, OperationError, ValidationError, HistoryError
from .calculator_config import load_config
from .calculator_memento import Caretaker
from .history import History, LoggingObserver, AutoSaveObserver
from .command_registry import command, resolve as resolve_cmd, all_specs, aliases_for


# Operation-only aliases (kept for REPL)
OP_ALIASES: Dict[str, str] = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "/": "divide",
    "//": "int_divide",
    "%": "modulus",
    "^": "power",
}


class Calculator:
    def __init__(self) -> None:
        cfg = load_config()
        self.cfg = cfg
        self.history = History(cfg.max_history_size)
        self.caretaker = Caretaker()

        # runtime precision (mutable)
        self.precision = cfg.precision

        # observers for logging/autosave
        self.log_observer = LoggingObserver()
        self.auto_observer = AutoSaveObserver()
        self.observers = [self.log_observer, self.auto_observer]

    def _notify(self, calc: Calculation) -> None:
        for ob in self.observers:
            ob.update(calc, self.history)

    def calculate(self, op_name: str, a: float, b: float) -> float:
        # Save snapshot before mutation (undo support)
        self.caretaker.save(self.history.to_snapshot())

        op = OperationFactory.create(op_name)
        result = op.execute(a, b)
        result = round(result, self.precision)

        calc = Calculation.from_values(op_name, a, b, result)
        self.history.add(calc)
        self._notify(calc)
        return result

    # --- History accessors (compat + explicit name) ---
    def cmd_history_items(self) -> List[Calculation]:
        """Return the current history list (new explicit name)."""
        return self.history.items()

    def cmd_history(self) -> List[Calculation]:
        """Backward-compatible alias used by older tests/code."""
        return self.cmd_history_items()

    # --- History operations ---
    def cmd_clear(self) -> None:
        self.caretaker.save(self.history.to_snapshot())
        self.history.clear()

    def cmd_undo(self) -> None:
        snap = self.caretaker.undo(self.history.to_snapshot())
        self.history.restore(snap)

    def cmd_redo(self) -> None:
        snap = self.caretaker.redo(self.history.to_snapshot())
        self.history.restore(snap)

    def cmd_save(self) -> str:
        return self.history.save_csv()

    def cmd_load(self) -> int:
        self.caretaker.save(self.history.to_snapshot())
        return self.history.load_csv()

    def cmd_get_precision(self) -> int:
        return self.precision

    def cmd_set_precision(self, n: int) -> int:
        if n < 0 or n > 18:
            raise ValidationError("Precision must be between 0 and 18.")
        self.precision = n
        return self.precision


# ---------------- Helper functions ---------------- #

def _suggest(cmd: str) -> str | None:
    candidates = set([spec.name for spec in all_specs()])
    candidates |= set(OP_ALIASES.keys())
    candidates |= set(OperationFactory.mapping.keys())
    matches = difflib.get_close_matches(cmd, sorted(candidates), n=1, cutoff=0.6)
    return matches[0] if matches else None


def _dynamic_help_text() -> str:
    lines: List[str] = ["Commands:"]
    for spec in all_specs():
        al = aliases_for(spec.name)
        alias_str = f" (aliases: {', '.join(al)})" if al else ""
        lines.append(f"  {spec.name:<12} - {spec.help}{alias_str}")

    ops = sorted(OperationFactory.mapping.keys())
    op_aliases = " ".join(OP_ALIASES.keys())
    lines.append("  ")
    lines.append("Operations:")
    lines.append("  " + "|".join(ops) + " a b")
    lines.append(f"\nOp aliases: {op_aliases}")
    lines.append("")  # trailing newline
    return "\n".join(lines)


# ---------------- Registered commands ---------------- #

@command("help", "show this help")
def _cmd_help(calc: Calculator, args: List[str]) -> None:
    print(_dynamic_help_text())

@command("history", "show history [N]")
def _cmd_history(calc: Calculator, args: List[str]) -> None:
    limit = None
    if args and args[0].isdigit():
        limit = int(args[0])
        if limit < 0:
            raise ValidationError("Limit must be non-negative.")
    items = calc.cmd_history_items()
    if limit is not None:
        items = items[-limit:]
    if not items:
        print(Fore.YELLOW + "(history is empty)")
    else:
        for i, c in enumerate(items, 1):
            print(f"{i}. {c.operation}({c.a}, {c.b}) = {c.result} @ {c.timestamp}")

@command("clear", "clear the history")
def _cmd_clear(calc: Calculator, args: List[str]) -> None:
    calc.cmd_clear()
    print(Fore.YELLOW + "History cleared.")

@command("undo", "undo last change")
def _cmd_undo(calc: Calculator, args: List[str]) -> None:
    calc.cmd_undo()
    print(Fore.YELLOW + "Undone.")

@command("redo", "redo last undone change")
def _cmd_redo(calc: Calculator, args: List[str]) -> None:
    calc.cmd_redo()
    print(Fore.YELLOW + "Redone.")

@command("save", "save history to CSV")
def _cmd_save(calc: Calculator, args: List[str]) -> None:
    path = calc.cmd_save()
    print(Fore.GREEN + f"Saved: {path}")

@command("load", "load history from CSV")
def _cmd_load(calc: Calculator, args: List[str]) -> None:
    n = calc.cmd_load()
    print(Fore.GREEN + f"Loaded {n} entries.")

@command("autosave", "toggle/show autosave status")
def _cmd_autosave(calc: Calculator, args: List[str]) -> None:
    if not args:
        print(Fore.CYAN + f"Auto-save is {'ON' if calc.auto_observer.is_enabled() else 'OFF'}")
    else:
        val = args[0].lower() in {"1", "true", "yes", "on", "y"}
        calc.auto_observer.set_enabled(val)
        print(Fore.CYAN + f"Auto-save set to {'ON' if val else 'OFF'}")

@command("precision", "show or set rounding precision (0..18)")
def _cmd_precision(calc: Calculator, args: List[str]) -> None:
    if not args:
        print(Fore.CYAN + f"Precision: {calc.cmd_get_precision()}")
    else:
        try:
            n = int(args[0])
        except ValueError:
            raise ValidationError("Precision must be an integer.")
        calc.cmd_set_precision(n)
        print(Fore.CYAN + f"Precision set to {n}")

@command("exit", "quit the application", aliases=["quit"])
def _cmd_exit(calc: Calculator, args: List[str]) -> None:
    print(Fore.CYAN + "Bye!")
    raise SystemExit


# ------------------------- REPL entrypoint ------------------------- #

def main() -> None:
    color_init(autoreset=True)
    calc = Calculator()
    print(Fore.CYAN + "Advanced Calculator (type 'help' for commands)")

    while True:
        try:
            line = input(Fore.WHITE + "> ").strip()
            if not line:
                continue
            parts = line.split()
            cmd_raw, args = parts[0], parts[1:]

            # 1) Decorator-registered commands first
            spec = resolve_cmd(cmd_raw.lower())
            if spec is not None:
                spec.handler(calc, args)
                continue

            # 2) Otherwise treat as arithmetic operation
            op = OP_ALIASES.get(cmd_raw.lower(), cmd_raw.lower())
            if op not in OperationFactory.mapping:
                raise OperationError(f"Unknown operation: {cmd_raw}")

            a, b = parse_two_numbers(args)
            result = calc.calculate(op, a, b)
            print(Fore.GREEN + f"Result: {result}")

        except (OperationError, ValidationError, HistoryError) as e:
            if isinstance(e, OperationError) and "Unknown operation" in str(e):
                suggestion = _suggest(cmd_raw.lower())
                msg = f"{e}"
                if suggestion:
                    msg += f" (did you mean '{suggestion}'?)"
                print(Fore.RED + f"Error: {msg}")
            else:
                print(Fore.RED + f"Error: {e}")
        except SystemExit:
            break
        except KeyboardInterrupt:
            print("\n" + Fore.CYAN + "Bye!")
            break
        except EOFError:
            print("\n" + Fore.CYAN + "Bye!")
            break
        except CalculatorError as e:
            print(Fore.RED + f"Calculator error: {e}")
        except Exception as e:
            print(Fore.RED + f"Unexpected error: {e}")


if __name__ == "__main__":
    main()