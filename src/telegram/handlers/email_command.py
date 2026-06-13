from aiogram import Router, F
from aiogram.types import Message

from src.constants import AT_SIGN
from src.env_tools import ADMIN_IDS, DOMAIN, RANDOM_KEY, SESSION_TTL_SECONDS
from src.infrastructure.in_memory_session_store import InMemorySessionStore
from src.services.email_address_service import normalize_address
from src.services.random_email_service import belongs_to_user
from src.services.session_service import register_session
from src.telegram.filters import EnabledUserFilter

EMAIL_CMD_ROUTER: Router = Router()

_MSG_WRONG_DOMAIN: str = "❌ Домен должен быть @{domain}. Получен: {received}"
_MSG_INVALID: str = "❌ Некорректный адрес: {reason}"
_MSG_START: str = "✅ Письма на {email} будут перенаправляться {minutes} мин."
_MSG_REPLACE: str = "🔄 Обновлено. Письма на {email} будут перенаправляться {minutes} мин."
_MSG_NOT_YOURS: str = "❌ Этот адрес не из вашего множества. Используйте /random чтобы получить свой адрес."
_MINUTES: int = SESSION_TTL_SECONDS // 60


def make_email_router(store: InMemorySessionStore) -> Router:
    @EMAIL_CMD_ROUTER.message(EnabledUserFilter(), F.text, ~F.text.startswith("/"))
    async def handle_email_input(message: Message) -> None:
        if message.from_user is None or message.text is None:
            return

        user_id = message.from_user.id

        try:
            normalized: str = normalize_address(message.text, DOMAIN)
        except SyntaxError as exc:
            reason = str(exc)
            if reason == DOMAIN:
                await message.answer(_MSG_WRONG_DOMAIN.format(domain=DOMAIN, received=reason))
            else:
                await message.answer(_MSG_INVALID.format(reason=reason))
            return

        if user_id not in ADMIN_IDS:
            if not belongs_to_user(RANDOM_KEY, user_id, normalized.split(AT_SIGN, 1)[0]):
                await message.answer(_MSG_NOT_YOURS)
                return

        had_session = await register_session(store, user_id, normalized, SESSION_TTL_SECONDS)
        template = _MSG_REPLACE if had_session else _MSG_START
        await message.answer(template.format(email=normalized, minutes=_MINUTES))

    return EMAIL_CMD_ROUTER
