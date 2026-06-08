from datetime import datetime, timezone
from typing import List, Optional, Union

from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiosmtpd.smtp import Envelope, Session, SMTP as SMTPProtocol

from src.logger import logger
from src.services.caption_service import build_caption
from src.services.filename_service import make_filename
from src.services.mail_parser import get_subject, to_html
from src.session.registry import SessionRegistry

_REPLY_OK: str = "250 OK"
_REPLY_NO_USER: str = "550 No such user"
_ENCODING: str = "utf-8"
_LOG_ACCEPTED: str = "smtp: accepted from %s to %s"
_LOG_REJECTED: str = "smtp: rejected from %s (no active sessions)"
_LOG_DELIVERED: str = "smtp: delivered %s to user %s"
_LOG_SEND_ERR: str = "smtp: send_document to %s failed: %s"


class MailHandler:
    def __init__(self, registry: SessionRegistry, bot: Bot) -> None:
        self._registry = registry
        self._bot = bot

    async def handle_RCPT(
        self,
        server: SMTPProtocol,
        session: Session,
        envelope: Envelope,
        address: str,
        rcpt_options: List[str],
    ) -> str:
        ip: str = session.peer[0] if session.peer else "?"
        if self._registry.find_user(address) is None:
            logger.info(_LOG_REJECTED, ip, address)
            return _REPLY_NO_USER
        logger.info(_LOG_ACCEPTED, ip, address)
        envelope.rcpt_tos.append(address)
        return _REPLY_OK

    async def handle_DATA(
        self,
        server: SMTPProtocol,
        session: Session,
        envelope: Envelope,
    ) -> str:
        raw_content: Union[str, bytes, None] = envelope.content
        if raw_content is None:
            return _REPLY_OK

        raw: bytes = (
            raw_content
            if isinstance(raw_content, bytes)
            else raw_content.encode(_ENCODING)
        )

        received_at: datetime = datetime.now(timezone.utc)
        sender: str = envelope.mail_from or ""
        ip: str = session.peer[0] if session.peer else "?"
        caption: str = build_caption(sender, ip, received_at)

        subject: Optional[str] = get_subject(raw)
        filename: str = make_filename(subject, sender)
        file_bytes: bytes = to_html(raw).encode(_ENCODING)

        for recipient in envelope.rcpt_tos:
            user_id = self._registry.find_user(recipient)
            if user_id is None:
                continue
            try:
                await self._bot.send_document(
                    chat_id=user_id,
                    document=BufferedInputFile(file_bytes, filename=filename),
                    caption=caption,
                    parse_mode="HTML",
                )
                logger.info(_LOG_DELIVERED, recipient, user_id)
            except Exception as exc:
                logger.error(_LOG_SEND_ERR, user_id, exc)

        return _REPLY_OK
