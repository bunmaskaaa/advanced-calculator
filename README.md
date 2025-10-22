# Advanced Calculator

A fully tested, extensible command-line calculator with:
- **Operations**: add, subtract, multiply, divide, power, root, modulus, int_divide, percent, abs_diff
- **Design patterns**: Factory (operations), Memento (undo/redo), Observer (logging + autosave)
- **REPL** with aliases (`+ - * / // % ^`), precision control, autosave toggle, history view/limit
- **Persistence**: CSV save/load with atomic writes & strict validation (pandas)
- **Logging**: File logging with configurable level
- **CI**: GitHub Actions matrix (3.10–3.13) with ≥90% coverage gate

---

## Quick Start

### 1) Clone
```bash
git clone https://github.com/<your-username>/advanced-calculator.git
cd advanced-calculator