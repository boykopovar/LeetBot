from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.env_tools import DOMAIN, RANDOM_KEY, SESSION_TTL_SECONDS
from src.infrastructure.in_memory_session_store import InMemorySessionStore
from src.services.random_email_service import generate_local, random_nonce
from src.services.session_service import register_session
from src.telegram.filters import EnabledUserFilter

RANDOM_CMD_ROUTER: Router = Router()

_AT: str = "@"
_MSG_READY: str = "🎲 Ваш адрес: {email}\nПисьма будут перенаправляться {minutes} мин."
_MSG_OVERFLOW: str = "Для вашего ID не можем выдать почту."
_MINUTES: int = SESSION_TTL_SECONDS // 60


def make_random_router(store: InMemorySessionStore) -> Router:
    @RANDOM_CMD_ROUTER.message(EnabledUserFilter(), Command("random", "start"))
    async def handle_random(message: Message) -> None:
        if message.from_user is None:
            return

        user_id = message.from_user.id
        try:
            local = generate_local(RANDOM_KEY, user_id, random_nonce())
        except OverflowError:
            await message.answer(_MSG_OVERFLOW)
            return

        email = local + _AT + DOMAIN
        await register_session(store, user_id, email, SESSION_TTL_SECONDS)
        await message.answer(_MSG_READY.format(email=email, minutes=_MINUTES))

    return RANDOM_CMD_ROUTER
