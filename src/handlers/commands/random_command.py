import asyncio

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.env_tools import DOMAIN, RANDOM_KEY, SESSION_MINUTES
from src.handlers.filters import EnabledUserFilter
from src.logger import logger
from src.services.random_email_service import generate_local, random_nonce
from src.session.registry import session_registry

RANDOM_CMD_ROUTER: Router = Router()

_AT: str = "@"
_MSG_READY: str = "🎲 Ваш адрес: {email}\nПисьма будут перенаправляться {minutes} мин."


async def _expiry_task(user_id: int, minutes: int) -> None:
    await asyncio.sleep(minutes * 60)
    session_registry.remove(user_id)
    logger.info("Session expired for user %s", user_id)


@RANDOM_CMD_ROUTER.message(EnabledUserFilter(), Command("random"))
async def handle_random(message: Message) -> None:
    if message.from_user is None:
        return

    user_id: int = message.from_user.id
    local: str = generate_local(RANDOM_KEY, user_id, random_nonce())
    email: str = local + _AT + DOMAIN
    task: asyncio.Task = asyncio.create_task(_expiry_task(user_id, SESSION_MINUTES))
    session_registry.register(user_id, email, task)
    await message.answer(_MSG_READY.format(email=email, minutes=SESSION_MINUTES))
