import logging
from typing import Optional

from src.logger import logger

_SMTP_LOGGERS: tuple = ("mail.log", "aiosmtpd.smtp", "aiosmtpd")

_MSG_ACCEPTED: str = "smtp: accepted from %s"
_MSG_REJECTED: str = "smtp: rejected (no active sessions) from %s"
_MSG_ERROR: str = "smtp: error from %s: %s"

_MARKER_ACCEPTED: str = "message from"
_MARKER_REJECTED: str = "not for us"
_MARKER_ERROR: str = "error"


def _peer_str(record: logging.LogRecord) -> str:
    args = record.args
    if isinstance(args, tuple) and args:
        return str(args[0])
    return record.getMessage()


class _SmtpNoiseFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg: str = record.getMessage().lower()
        if _MARKER_ACCEPTED in msg:
            logger.info(_MSG_ACCEPTED, _peer_str(record))
        elif _MARKER_REJECTED in msg:
            logger.info(_MSG_REJECTED, _peer_str(record))
        elif _MARKER_ERROR in msg:
            logger.error(_MSG_ERROR, _peer_str(record), record.getMessage())
        return False


def suppress_smtp_noise() -> None:
    filt = _SmtpNoiseFilter()
    for name in _SMTP_LOGGERS:
        log = logging.getLogger(name)
        log.setLevel(logging.DEBUG)
        log.addFilter(filt)
        log.propagate = False
