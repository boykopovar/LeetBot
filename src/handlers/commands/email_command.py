import asyncio
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message
from email_validator import EmailNotValidError, validate_email

from src.env_tools import ADMIN_IDS, DOMAIN, RANDOM_KEY, SESSION_MINUTES
from src.handlers.filters import EnabledUserFilter
from src.logger import logger
from src.services.random_email_service import belongs_to_user
from src.session.registry import session_registry

EMAIL_CMD_ROUTER: Router = Router()

_AT: str = "@"
_MSG_WRONG_DOMAIN: str = "❌ Домен должен быть @{domain}. Получен: {received}"
_MSG_INVALID: str = "❌ Некорректный адрес: {reason}"
_MSG_START: str = "✅ Письма на {email} будут перенаправляться {minutes} мин."
_MSG_REPLACE: str = "🔄 Обновлено. Письма на {email} будут перенаправляться {minutes} мин."
_MSG_NOT_YOURS: str = "❌ Этот адрес не из вашего множества. Используйте /random чтобы получить свой адрес."


async def _expiry_task(user_id: int, minutes: int) -> None:
    await asyncio.sleep(minutes * 60)
    session_registry.remove(user_id)
    logger.info(f"Session expired for user {user_id}")


def _register(user_id: int, normalized: str) -> bool:
    had_session: bool = session_registry.get_email(user_id) is not None
    task: asyncio.Task = asyncio.create_task(_expiry_task(user_id, SESSION_MINUTES))
    session_registry.register(user_id, normalized, task)
    return had_session


async def _parse_and_validate(message: Message) -> Optional[str]:
    raw: str = message.text.strip()  # type: ignore[union-attr]
    has_at: bool = _AT in raw
    address: str = raw if has_at else raw + _AT + DOMAIN

    try:
        info = validate_email(address, check_deliverability=False)
    except EmailNotValidError as exc:
        await message.answer(_MSG_INVALID.format(reason=str(exc)))
        return None

    if has_at and info.domain.lower() != DOMAIN:
        await message.answer(_MSG_WRONG_DOMAIN.format(domain=DOMAIN, received=info.domain))
        return None

    return info.normalized


@EMAIL_CMD_ROUTER.message(EnabledUserFilter(), F.text, ~F.text.startswith("/"))
async def handle_email_input(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    user_id: int = message.from_user.id
    normalized: Optional[str] = await _parse_and_validate(message)
    if normalized is None:
        return

    if user_id not in ADMIN_IDS:
        if not belongs_to_user(RANDOM_KEY, user_id, normalized.split(_AT)[0]):
            await message.answer(_MSG_NOT_YOURS)
            return

    had_session: bool = _register(user_id, normalized)
    template: str = _MSG_REPLACE if had_session else _MSG_START
    await message.answer(template.format(email=normalized, minutes=SESSION_MINUTES))
