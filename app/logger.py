import logging
from .calculator_config import load_config
import os

def _level_from_env(default: str = "INFO") -> int:
    level = os.getenv("CALCULATOR_LOG_LEVEL", default).upper()
    return {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
    }.get(level, logging.INFO)

def get_logger() -> logging.Logger:
    """
    Return a logger that always writes to the current config's log file.
    If handlers point to a different file from a prior run, rewire them.
    Respects CALCULATOR_LOG_LEVEL (default INFO).
    """
    cfg = load_config()
    logger = logging.getLogger("calculator")
    logger.setLevel(_level_from_env())

    desired_path = cfg.log_file
    need_file_handler = True

    # Remove file handlers pointing elsewhere
    for h in list(logger.handlers):
        if isinstance(h, logging.FileHandler):
            if getattr(h, "baseFilename", None) == desired_path:
                need_file_handler = False
            else:
                logger.removeHandler(h)
                try:
                    h.close()
                except Exception:
                    pass

    if need_file_handler:
        fh = logging.FileHandler(desired_path, encoding=cfg.default_encoding)
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger