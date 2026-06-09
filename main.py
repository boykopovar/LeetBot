import asyncio
import logging
import signal
from types import FrameType
from typing import Optional

import uvicorn
from aiogram import Bot, Dispatcher

from src.api.app import create_app
from src.env_tools import (
    API_HOST,
    API_PORT,
    BOT_TOKEN,
    RANDOM_KEY,
    SMTP_HOST,
    SMTP_PORT,
    TOKEN_TTL_DAYS,
)
from src.infrastructure.in_memory_session_store import InMemorySessionStore
from src.logger import logger
from src.services.token_service import JwtTokenService
from src.smtp.handler import MailHandler
from src.smtp.log_filter import suppress_smtp_noise
from src.smtp.server import start_smtp_server
from src.telegram.router import register_all_routers

logging.getLogger("aiogram.event").setLevel(logging.WARNING)
suppress_smtp_noise()


async def _run_api(store: InMemorySessionStore, signer: JwtTokenService) -> None:
    app = create_app(store, signer)
    config = uvicorn.Config(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    store = InMemorySessionStore()
    signer = JwtTokenService(key=RANDOM_KEY, token_ttl_days=TOKEN_TTL_DAYS)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    register_all_routers(dp, store, signer, TOKEN_TTL_DAYS)

    mail_handler = MailHandler(store=store, bot=bot)
    smtp_server = await start_smtp_server(
        handler=mail_handler,
        store=store,
        host=SMTP_HOST,
        port=SMTP_PORT,
    )
    logger.info(f"SMTP on {SMTP_HOST}:{SMTP_PORT}")
    logger.info(f"API on {API_HOST}:{API_PORT}")

    try:
        await asyncio.gather(
            dp.start_polling(bot, handle_signals=False),
            _run_api(store, signer),
        )
    finally:
        smtp_server.close()
        await smtp_server.wait_closed()


def _exit_prog(sig: int, frame: Optional[FrameType]) -> None:
    import os
    os._exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _exit_prog)
    signal.signal(signal.SIGTERM, _exit_prog)
    asyncio.run(main())
