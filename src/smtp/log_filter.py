import logging

_SMTP_LOGGERS: tuple = ("mail.log", "aiosmtpd.smtp", "aiosmtpd")


class _DropAll(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return False


def suppress_smtp_noise() -> None:
    filt = _DropAll()
    for name in _SMTP_LOGGERS:
        log = logging.getLogger(name)
        log.addFilter(filt)
        log.propagate = False
