from aiogram.filters import BaseFilter
from aiogram.types import Message

from src.env_tools import ENABLED_IDS


class EnabledUserFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return (
            message.from_user is not None
            and message.from_user.id in ENABLED_IDS
        )
