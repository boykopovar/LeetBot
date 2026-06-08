import asyncio

from aiogram import Router
from aiogram.types import Message
from email_validator import EmailNotValidError, validate_email

from src.env_tools import DOMAIN, SESSION_MINUTES
from src.handlers.filters import EnabledUserFilter
from src.logger import logger
from src.session.registry import session_registry

EMAIL_CMD_ROUTER: Router = Router()

_AT: str = "@"
_MSG_WRONG_DOMAIN: str = "❌ Домен должен быть @{domain}. Получен: {received}"
_MSG_INVALID: str = "❌ Некорректный адрес: {reason}"
_MSG_START: str = "✅ Письма на {email} будут перенаправляться {minutes} мин."
_MSG_REPLACE: str = "🔄 Обновлено. Письма на {email} будут перенаправляться {minutes} мин."


async def _expiry_task(user_id: int, minutes: int) -> None:
    await asyncio.sleep(minutes * 60)
    session_registry.remove(user_id)
    logger.info("Session expired for user %s", user_id)


@EMAIL_CMD_ROUTER.message(EnabledUserFilter())
async def handle_email_input(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    user_id: int = message.from_user.id
    raw: str = message.text.strip()
    has_at: bool = _AT in raw
    address: str = raw if has_at else raw + _AT + DOMAIN

    try:
        info = validate_email(address, check_deliverability=False)
    except EmailNotValidError as exc:
        await message.answer(_MSG_INVALID.format(reason=str(exc)))
        return

    if has_at and info.domain.lower() != DOMAIN:
        await message.answer(
            _MSG_WRONG_DOMAIN.format(domain=DOMAIN, received=info.domain)
        )
        return

    normalized: str = info.normalized
    had_session: bool = session_registry.get_email(user_id) is not None
    task: asyncio.Task = asyncio.create_task(_expiry_task(user_id, SESSION_MINUTES))
    session_registry.register(user_id, normalized, task)

    template: str = _MSG_REPLACE if had_session else _MSG_START
    await message.answer(template.format(email=normalized, minutes=SESSION_MINUTES))
