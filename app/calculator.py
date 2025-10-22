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


COMMANDS = {
    "add", "subtract", "multiply", "divide", "power", "root",
    "modulus", "int_divide", "percent", "abs_diff",
    "history", "clear", "undo", "redo", "save", "load",
    "help", "exit", "autosave", "precision"
}

# REPL-only aliases (translated before execution)
ALIASES: Dict[str, str] = {
    "+": "add",
    "-": "subtract",
    "*": "multiply",
    "/": "divide",
    "//": "int_divide",
    "%": "modulus",
    "^": "power",
    "quit": "exit",
}


class Calculator:
    def __init__(self) -> None:
        cfg = load_config()
        self.cfg = cfg
        self.history = History(cfg.max_history_size)
        self.caretaker = Caretaker()

        # runtime precision (mutable; default from config)
        self.precision = cfg.precision

        # Keep explicit references so we can toggle autosave at runtime
        self.log_observer = LoggingObserver()
        self.auto_observer = AutoSaveObserver()
        self.observers = [self.log_observer, self.auto_observer]

    def _notify(self, calc: Calculation) -> None:
        for ob in self.observers:
            ob.update(calc, self.history)

    def calculate(self, op_name: str, a: float, b: float) -> float:
        # Save snapshot before mutating, for undo
        self.caretaker.save(self.history.to_snapshot())

        op = OperationFactory.create(op_name)
        result = op.execute(a, b)
        # round using mutable runtime precision
        result = round(result, self.precision)

        calc = Calculation.from_values(op_name, a, b, result)
        self.history.add(calc)
        self._notify(calc)
        return result

    # ----- Command helpers -----
    def cmd_history(self) -> List[Calculation]:
        return self.history.items()

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
        # loading replaces history (take snapshot for undo)
        self.caretaker.save(self.history.to_snapshot())
        return self.history.load_csv()

    def cmd_get_precision(self) -> int:
        return self.precision

    def cmd_set_precision(self, n: int) -> int:
        if n < 0 or n > 18:
            # guardrail; pandas/float formatting gets messy beyond this
            raise ValidationError("Precision must be between 0 and 18.")
        self.precision = n
        return self.precision


def _help() -> str:
    return (
        "Commands:\n"
        "  add|subtract|multiply|divide|power|root|modulus|int_divide|percent|abs_diff a b\n"
        "  history [N]     - show history (optionally last N)\n"
        "  clear           - clear history\n"
        "  undo            - undo last change\n"
        "  redo            - redo last undone change\n"
        "  save            - save history to CSV\n"
        "  load            - load history from CSV\n"
        "  autosave [on|off] - toggle or show autosave status\n"
        "  precision [N]   - show or set rounding precision (0..18)\n"
        "  help            - show this help\n"
        "  exit | quit     - quit\n"
        "\nAliases for ops: +  -  *  /  //  %  ^\n"
    )


def _suggest(cmd: str) -> str | None:
    # Suggest close commands for typos
    candidates = list(COMMANDS | set(ALIASES.keys()))
    matches = difflib.get_close_matches(cmd, candidates, n=1, cutoff=0.6)
    return matches[0] if matches else None


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
            cmd = ALIASES.get(cmd_raw.lower(), cmd_raw.lower())

            if cmd in {"exit", "quit"}:
                print(Fore.CYAN + "Bye!")
                break

            elif cmd == "help":
                print(_help())
                continue

            elif cmd == "history":
                limit = None
                if args and args[0].isdigit():
                    limit = int(args[0])
                    if limit < 0:
                        raise ValidationError("Limit must be non-negative.")
                items = calc.cmd_history()
                if limit is not None:
                    items = items[-limit:]
                if not items:
                    print(Fore.YELLOW + "(history is empty)")
                else:
                    for i, c in enumerate(items, 1):
                        print(f"{i}. {c.operation}({c.a}, {c.b}) = {c.result} @ {c.timestamp}")
                continue

            elif cmd == "clear":
                calc.cmd_clear()
                print(Fore.YELLOW + "History cleared.")
                continue

            elif cmd == "undo":
                calc.cmd_undo()
                print(Fore.YELLOW + "Undone.")
                continue

            elif cmd == "redo":
                calc.cmd_redo()
                print(Fore.YELLOW + "Redone.")
                continue

            elif cmd == "save":
                path = calc.cmd_save()
                print(Fore.GREEN + f"Saved: {path}")
                continue

            elif cmd == "load":
                n = calc.cmd_load()
                print(Fore.GREEN + f"Loaded {n} entries.")
                continue

            elif cmd == "autosave":
                if not args:
                    print(
                        Fore.CYAN
                        + f"Auto-save is {'ON' if calc.auto_observer.is_enabled() else 'OFF'}"
                    )
                else:
                    val = args[0].lower() in {"1", "true", "yes", "on", "y"}
                    calc.auto_observer.set_enabled(val)
                    print(Fore.CYAN + f"Auto-save set to {'ON' if val else 'OFF'}")
                continue

            elif cmd == "precision":
                if not args:
                    print(Fore.CYAN + f"Precision: {calc.cmd_get_precision()}")
                else:
                    try:
                        n = int(args[0])
                    except ValueError:
                        raise ValidationError("Precision must be an integer.")
                    calc.cmd_set_precision(n)
                    print(Fore.CYAN + f"Precision set to {n}")
                continue

            else:
                # ---- OPERATION PATH (with early unknown-op check) ----
                # If it's not a known operation name, fail *before* parsing operands.
                if cmd not in OperationFactory.mapping:
                    raise OperationError(f"Unknown operation: {cmd}")

                # operation commands (+ aliases handled already)
                a, b = parse_two_numbers(args)
                result = calc.calculate(cmd, a, b)
                print(Fore.GREEN + f"Result: {result}")

        except (OperationError, ValidationError, HistoryError) as e:
            # spell-check suggestion for unknown commands
            if isinstance(e, OperationError) and "Unknown operation" in str(e):
                suggestion = _suggest(cmd)
                msg = f"{e}"
                if suggestion:
                    msg += f" (did you mean '{suggestion}'?)"
                print(Fore.RED + f"Error: {msg}")
            else:
                print(Fore.RED + f"Error: {e}")
        except KeyboardInterrupt:  # pragma: no cover
            print("\n" + Fore.CYAN + "Bye!")
            break
        except EOFError:  # pragma: no cover
            print("\n" + Fore.CYAN + "Bye!")
            break
        except CalculatorError as e:  # pragma: no cover
            print(Fore.RED + f"Calculator error: {e}")
        except Exception as e:  # pragma: no cover
            print(Fore.RED + f"Unexpected error: {e}")


if __name__ == "__main__":  # pragma: no cover
    main()