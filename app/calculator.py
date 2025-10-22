from __future__ import annotations
from typing import List
from colorama import init as color_init, Fore, Style
from .operations import OperationFactory
from .input_validators import parse_two_numbers
from .calculation import Calculation
from .exceptions import CalculatorError, OperationError, ValidationError, HistoryError
from .calculator_config import load_config
from .calculator_memento import Caretaker
from .history import History, LoggingObserver, AutoSaveObserver

class Calculator:
    def __init__(self) -> None:
        cfg = load_config()
        self.cfg = cfg
        self.history = History(cfg.max_history_size)
        self.caretaker = Caretaker()

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
        # rounding for stored result can be consistent
        result = round(result, self.cfg.precision)

        calc = Calculation.from_values(op_name, a, b, result)
        self.history.add(calc)
        self._notify(calc)
        return result

    # Commands
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

def _help() -> str:
    return (
        "Commands:\n"
        "  add|subtract|multiply|divide|power|root|modulus|int_divide|percent|abs_diff a b\n"
        "  history         - show calculation history\n"
        "  clear           - clear history\n"
        "  undo            - undo last change\n"
        "  redo            - redo last undone change\n"
        "  save            - save history to CSV\n"
        "  load            - load history from CSV\n"
        "  autosave [on|off] - toggle or show autosave status\n"
        "  help            - show this help\n"
        "  exit            - quit\n"
    )

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
            cmd, args = parts[0].lower(), parts[1:]

            if cmd == "exit":
                print(Fore.CYAN + "Bye!")
                break

            elif cmd == "help":
                print(_help())
                continue

            elif cmd == "history":
                for i, c in enumerate(calc.cmd_history(), 1):
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

            # --- NEW: autosave toggle/show ---
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

            else:
                # operation commands
                a, b = parse_two_numbers(args)
                result = calc.calculate(cmd, a, b)
                print(Fore.GREEN + f"Result: {result}")

        except (OperationError, ValidationError, HistoryError) as e:
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