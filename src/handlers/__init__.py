from aiogram import Dispatcher

from src.handlers.commands import CMD_ROUTER


def register_all_routers(dp: Dispatcher) -> None:
    dp.include_router(CMD_ROUTER)
