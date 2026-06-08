from aiogram import Router

from src.handlers.commands.email_command import EMAIL_CMD_ROUTER

CMD_ROUTER: Router = Router()
CMD_ROUTER.include_router(EMAIL_CMD_ROUTER)
