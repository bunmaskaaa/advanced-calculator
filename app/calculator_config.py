from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass(frozen=True)
class Config:
    log_dir: str
    history_dir: str
    max_history_size: int
    auto_save: bool
    precision: int
    max_input_value: float
    default_encoding: str
    log_file: str
    history_file: str

def load_config() -> Config:
    load_dotenv()
    log_dir = os.getenv("CALCULATOR_LOG_DIR", ".logs")
    history_dir = os.getenv("CALCULATOR_HISTORY_DIR", ".history")
    max_history_size = int(os.getenv("CALCULATOR_MAX_HISTORY_SIZE", "1000"))
    auto_save = os.getenv("CALCULATOR_AUTO_SAVE", "true").lower() in {"1", "true", "yes", "y"}
    precision = int(os.getenv("CALCULATOR_PRECISION", "6"))
    max_input_value = float(os.getenv("CALCULATOR_MAX_INPUT_VALUE", "1e12"))
    default_encoding = os.getenv("CALCULATOR_DEFAULT_ENCODING", "utf-8")

    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "calculator.log")
    history_file = os.path.join(history_dir, "history.csv")

    return Config(
        log_dir=log_dir,
        history_dir=history_dir,
        max_history_size=max_history_size,
        auto_save=auto_save,
        precision=precision,
        max_input_value=max_input_value,
        default_encoding=default_encoding,
        log_file=log_file,
        history_file=history_file,
    )