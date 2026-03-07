from __future__ import annotations

from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import sys


def setup_logging() -> Path:
    log_dir = Path.home() / ".wafw00f-gui" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return log_file

    root_logger.setLevel(logging.INFO)
    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    def _handle_exception(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: object) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.getLogger(__name__).exception("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = _handle_exception
    return log_file
