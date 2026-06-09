import asyncio

from aiosmtpd.smtp import SMTP

from src.ports.session_store import SessionStore
from src.smtp.handler import MailHandler


class _RejectProtocol(asyncio.Protocol):
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
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
