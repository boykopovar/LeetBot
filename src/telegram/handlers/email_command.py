from typing import Optional

from aiogram import Router, F
from aiogram.types import Message
from email_validator import EmailNotValidError, validate_email

from src.env_tools import ADMIN_IDS, DOMAIN, RANDOM_KEY, SESSION_TTL_SECONDS
from src.infrastructure.in_memory_session_store import InMemorySessionStore
from src.services.random_email_service import belongs_to_user
from src.services.session_service import register_session
from src.telegram.filters import EnabledUserFilter

EMAIL_CMD_ROUTER: Router = Router()

_AT: str = "@"
_MSG_WRONG_DOMAIN: str = "❌ Домен должен быть @{domain}. Получен: {received}"
_MSG_INVALID: str = "❌ Некорректный адрес: {reason}"
_MSG_START: str = "✅ Письма на {email} будут перенаправляться {minutes} мин."
_MSG_REPLACE: str = "🔄 Обновлено. Письма на {email} будут перенаправляться {minutes} мин."
_MSG_NOT_YOURS: str = "❌ Этот адрес не из вашего множества. Используйте /random чтобы получить свой адрес."
_MINUTES: int = SESSION_TTL_SECONDS // 60


async def _parse_and_validate(text: str, message: Message) -> Optional[str]:
    raw = text.strip()
    has_at = _AT in raw
    address = raw if has_at else raw + _AT + DOMAIN

    try:
        info = validate_email(address, check_deliverability=False)
    except EmailNotValidError as exc:
        await message.answer(_MSG_INVALID.format(reason=str(exc)))
        return None

    if has_at and info.domain.lower() != DOMAIN:
        await message.answer(_MSG_WRONG_DOMAIN.format(domain=DOMAIN, received=info.domain))
        return None

    return info.normalized


def make_email_router(store: InMemorySessionStore) -> Router:
    @EMAIL_CMD_ROUTER.message(EnabledUserFilter(), F.text, ~F.text.startswith("/"))
    async def handle_email_input(message: Message) -> None:
        if message.from_user is None or message.text is None:
            return

        user_id = message.from_user.id
        normalized = await _parse_and_validate(message.text, message)
        if normalized is None:
            return

        if user_id not in ADMIN_IDS:
            if not belongs_to_user(RANDOM_KEY, user_id, normalized.split(_AT)[0]):
                await message.answer(_MSG_NOT_YOURS)
                return

        had_session = await register_session(store, user_id, normalized, SESSION_TTL_SECONDS)
        template = _MSG_REPLACE if had_session else _MSG_START
        await message.answer(template.format(email=normalized, minutes=_MINUTES))

    return EMAIL_CMD_ROUTER
