from aiogram import Dispatcher

from src.handlers.commands import CMD_ROUTER
from src.handlers.middleware import UpdateLogMiddleware


def register_all_routers(dp: Dispatcher) -> None:
    dp.update.outer_middleware(UpdateLogMiddleware())
    dp.include_router(CMD_ROUTER)
