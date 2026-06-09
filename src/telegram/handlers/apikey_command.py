from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.constants import PARSE_MODE_HTML
from src.ports.token_signer import TokenSigner
from src.telegram.filters import EnabledUserFilter

APIKEY_CMD_ROUTER: Router = Router()

_MSG_KEY: str = (
    "🔑 Ваш API-ключ (действителен {days} дн.):\n\n"
    "<code>{token}</code>\n\n"
    "Используйте заголовок:\n"
    "<code>Authorization: Bearer {token}</code>"
)
_MSG_EXPIRED_NOTE: str = "⚠️ Предыдущий ключ становится недействительным."


def make_apikey_router(signer: TokenSigner, ttl_days: int) -> Router:
    @APIKEY_CMD_ROUTER.message(EnabledUserFilter(), Command("apikey"))
    async def handle_apikey(message: Message) -> None:
        if message.from_user is None:
            return
        token = signer.sign(message.from_user.id)
        await message.answer(
            _MSG_KEY.format(token=token, days=ttl_days),
            parse_mode=PARSE_MODE_HTML,
        )

    return APIKEY_CMD_ROUTER
