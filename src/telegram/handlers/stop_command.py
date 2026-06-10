from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.infrastructure.in_memory_session_store import InMemorySessionStore
from src.services.session_service import stop_session
from src.telegram.filters import EnabledUserFilter

STOP_CMD_ROUTER: Router = Router()

_MSG_STOPPED: str = "🛑 Сессия завершена."
_MSG_NO_SESSION: str = "ℹ️ Активной сессии нет."


def make_stop_router(store: InMemorySessionStore) -> Router:
    @STOP_CMD_ROUTER.message(EnabledUserFilter(), Command("stop"))
    async def handle_stop(message: Message) -> None:
        if message.from_user is None:
            return
        stopped = stop_session(store, message.from_user.id)
        await message.answer(_MSG_STOPPED if stopped else _MSG_NO_SESSION)

    return STOP_CMD_ROUTER
