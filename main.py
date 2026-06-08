import asyncio
import logging
import os
import signal
from types import FrameType
from typing import Optional

from aiogram import Bot, Dispatcher

from src.env_tools import SMTP_HOST, SMTP_PORT, TOKEN
from src.handlers import register_all_routers
from src.logger import logger
from src.session.registry import session_registry
from src.smtp.handler import MailHandler
from src.smtp.server import start_smtp_server

logging.getLogger("aiogram.event").setLevel(logging.WARNING)


async def main() -> None:
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    register_all_routers(dp)

    mail_handler = MailHandler(registry=session_registry, bot=bot)
    smtp_server = await start_smtp_server(
        handler=mail_handler,
        registry=session_registry,
        host=SMTP_HOST,
        port=SMTP_PORT,
    )
    logger.info("SMTP %s:%s", SMTP_HOST, SMTP_PORT)

    try:
        await dp.start_polling(bot, handle_signals=False)
    finally:
        smtp_server.close()
        await smtp_server.wait_closed()


def exit_prog(sig: int, frame: Optional[FrameType]) -> None:
    os._exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_prog)
    signal.signal(signal.SIGTERM, exit_prog)
    asyncio.run(main())
