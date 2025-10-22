import logging
from .calculator_config import load_config

def get_logger() -> logging.Logger:
    """
    Return a logger that always writes to the current config's log file.
    If handlers point to a different file from a prior run, rewire them.
    """
    cfg = load_config()
    logger = logging.getLogger("calculator")
    logger.setLevel(logging.INFO)

    desired_path = cfg.log_file
    need_file_handler = True

    # Remove any existing FileHandlers pointing to a different file
    for h in list(logger.handlers):
        if isinstance(h, logging.FileHandler):
            # If already pointing to the right file, keep it.
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