from aiogram import Router

from src.handlers.commands.email_command import EMAIL_CMD_ROUTER
from src.handlers.commands.random_command import RANDOM_CMD_ROUTER

CMD_ROUTER: Router = Router()
CMD_ROUTER.include_router(EMAIL_CMD_ROUTER)
CMD_ROUTER.include_router(RANDOM_CMD_ROUTER)
