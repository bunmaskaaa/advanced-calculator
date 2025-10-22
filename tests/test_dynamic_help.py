from app.command_registry import command, resolve, all_specs
from app.calculator import main, Calculator
import builtins
import io
from contextlib import redirect_stdout

# Dynamically add a command only for the test
@command("echo", "echo back args", aliases=["say"])
def _echo(calc, args):
    print("ECHO:" + " ".join(args))

def run_with_inputs(lines, monkeypatch):
    it = iter(lines)
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(it))
    buf = io.StringIO()
    with redirect_stdout(buf):
        main()
    return buf.getvalue()

def test_dynamic_help_lists_new_command(monkeypatch, tmp_path):
    # set dirs to isolate FS
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path / "hist"))
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path / "logs"))

    out = run_with_inputs(["help", "echo hello world", "say 1 2 3", "exit"], monkeypatch)
    # help should contain our dynamically registered command
    assert "echo" in out and "aliases: say" in out
    # both canonical and alias should work
    assert "ECHO:hello world" in out
    assert "ECHO:1 2 3" in out