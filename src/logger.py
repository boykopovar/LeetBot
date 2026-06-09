import logging
import time
from typing import Optional

from src.constants import ENCODING_UTF8
from src.env_tools import LOG_FILE

_FMT_DEFAULT: str = "%(asctime)s - %(levelname)s - %(message)s"
_FMT_ERROR: str = "%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s"
_DATEFMT: str = "%d.%m.%y %H:%M"


class LevelFormatter(logging.Formatter):
    def __init__(
        self,
        fmt_default: str,
        fmt_err: str,
        datefmt: Optional[str] = None,
    ) -> None:
        super().__init__(datefmt=datefmt)
        self.default_formatter = logging.Formatter(fmt_default, datefmt)
        self.default_formatter.converter = time.gmtime
        self.error_formatter = logging.Formatter(fmt_err, datefmt)
        self.error_formatter.converter = time.gmtime

    def format(self, record: logging.LogRecord) -> str:
        if record.levelno >= logging.ERROR:
            return self.error_formatter.format(record)
        return self.default_formatter.format(record)


_formatter = LevelFormatter(
    fmt_default=_FMT_DEFAULT,
    fmt_err=_FMT_ERROR,
    datefmt=_DATEFMT,
)

_root = logging.getLogger()
_root.setLevel(logging.INFO)

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_formatter)

_file_handler = logging.FileHandler(LOG_FILE, encoding=ENCODING_UTF8)
_file_handler.setLevel(logging.WARNING)
_file_handler.setFormatter(_formatter)

_root.addHandler(_console_handler)
_root.addHandler(_file_handler)

logger = logging.getLogger(__name__)
