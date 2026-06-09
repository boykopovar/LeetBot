import time
from typing import Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, Update, User

from src.logger import logger

_AVG_ALPHA: float = 0.1
_CONTENT_MAX: int = 100
_TYPE_CB: str = "cb"
_TYPE_MSG: str = "msg"
_UNKNOWN_USER: str = "?"
_EVENT_CB: str = "callback_query"
_EVENT_MSG: str = "message"

_avg_handle_time: float = 0.0


def get_avg_handle_time() -> float:
    return _avg_handle_time


def _update_avg(ms: int) -> None:
    global _avg_handle_time
    if _avg_handle_time == 0.0:
        _avg_handle_time = float(ms)
    else:
        _avg_handle_time = _avg_handle_time * (1.0 - _AVG_ALPHA) + ms * _AVG_ALPHA


def _format_user(user: Optional[User]) -> str:
    if user is None:
        return _UNKNOWN_USER
    if user.username:
        return f"@{user.username}"
    parts = [user.first_name or "", user.last_name or ""]
    full = " ".join(p for p in parts if p)
    return full if full else str(user.id)


def _extract_user(event: Update) -> Optional[User]:
    if event.message:
        return event.message.from_user
    if event.callback_query:
        return event.callback_query.from_user
    return None


def _extract_content(event: Update) -> str:
    if event.callback_query:
        return event.callback_query.data or ""

    msg: Optional[Message] = event.message
    if msg is None:
        return ""
    if msg.text:
        return msg.text
    if msg.caption:
        return f"[media] {msg.caption}"
    if msg.document:
        return f"[document: {msg.document.file_name}]"
    if msg.photo:
        return "[photo]"
    if msg.video:
        return "[video]"
    if msg.audio:
        return "[audio]"
    if msg.voice:
        return "[voice]"
    if msg.sticker:
        return f"[sticker: {msg.sticker.emoji or ''}]"
    if msg.animation:
        return "[gif]"
    return "[unknown]"


def _event_type_label(event: Update) -> str:
    if event.event_type == _EVENT_CB:
        return _TYPE_CB
    if event.event_type == _EVENT_MSG:
        return _TYPE_MSG
    return event.event_type


class UpdateLogMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, object]], Awaitable[object]],
        event: Update,
        data: Dict[str, object],
    ) -> object:
        start: float = time.perf_counter()
        try:
            return await handler(event, data)
        finally:
            ms: int = int((time.perf_counter() - start) * 1000)
            user: Optional[User] = _extract_user(event)
            user_repr: str = str(user.id) if user else _UNKNOWN_USER
            name: str = _format_user(user)
            content: str = _extract_content(event)
            content_str: str = f" '{content[:_CONTENT_MAX]}'" if content else ""
            label: str = _event_type_label(event)
            logger.info(f"{label}: {ms}ms from ({user_repr}) {name}:{content_str}")
            _update_avg(ms)
