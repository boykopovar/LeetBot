from datetime import datetime, timezone

_LABEL_FROM: str = "📨 <b>Отправитель:</b>"
_LABEL_IP: str = "🌐 <b>IP:</b>"
_LABEL_RECEIVED: str = "🕐 <b>Получено:</b>"
_DT_FMT: str = "%d.%m.%Y %H:%M:%S UTC"
_AGO_NOW: str = "только что"
_AGO_SEC: str = "{v} сек. назад"
_AGO_MIN: str = "{v} мин. назад"
_AGO_HOUR: str = "{h} ч. {m} мин. назад"
_AGO_DAY: str = "{d} д. {h} ч. назад"

_SECS_PER_MIN: int = 60
_SECS_PER_HOUR: int = 3600
_SECS_PER_DAY: int = 86400
_THRESHOLD_NOW: int = 5


def format_elapsed(seconds: int) -> str:
    if seconds < _THRESHOLD_NOW:
        return _AGO_NOW
    if seconds < _SECS_PER_MIN:
        return _AGO_SEC.format(v=seconds)
    if seconds < _SECS_PER_HOUR:
        return _AGO_MIN.format(v=seconds // _SECS_PER_MIN)
    if seconds < _SECS_PER_DAY:
        return _AGO_HOUR.format(
            h=seconds // _SECS_PER_HOUR,
            m=(seconds % _SECS_PER_HOUR) // _SECS_PER_MIN,
        )
    return _AGO_DAY.format(
        d=seconds // _SECS_PER_DAY,
        h=(seconds % _SECS_PER_DAY) // _SECS_PER_HOUR,
    )


def build_caption(sender: str, ip: str, received_at: datetime) -> str:
    elapsed: int = int((datetime.now(timezone.utc) - received_at).total_seconds())
    time_str: str = received_at.strftime(_DT_FMT)
    ago_str: str = format_elapsed(elapsed)
    lines = [
        f"{_LABEL_FROM} {sender}",
        f"{_LABEL_IP} {ip}",
        f"{_LABEL_RECEIVED} {time_str} ({ago_str})",
    ]
    return "\n".join(lines)
