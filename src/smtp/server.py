import asyncio
from typing import Optional, Tuple

from aiosmtpd.smtp import SMTP

from src.logger import logger
from src.ports.session_store import SessionStore
from src.smtp.handler import MailHandler

_LOG_REJECTED_IDLE: str = "smtp: rejected {ip} (no active sessions, connection closed)"


class _RejectProtocol(asyncio.Protocol):
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        peer: Optional[Tuple[str, int]] = transport.get_extra_info("peername")
        ip: str = peer[0] if peer else "?"
        logger.info(_LOG_REJECTED_IDLE.format(ip=ip))
        transport.close()


async def start_smtp_server(
    handler: MailHandler,
    store: SessionStore,
    host: str,
    port: int,
) -> asyncio.AbstractServer:
    loop = asyncio.get_running_loop()

    def factory() -> asyncio.Protocol:
        if not store.has_active():
            return _RejectProtocol()
        return SMTP(handler)

    return await loop.create_server(factory, host=host, port=port)
