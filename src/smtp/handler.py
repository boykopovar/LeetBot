from datetime import datetime, timezone
from typing import List, Optional, Union

from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiosmtpd.smtp import Envelope, Session, SMTP as SMTPProtocol

from src.constants import ENCODING_UTF8, PARSE_MODE_HTML
from src.domain.mail_message import MailMessage
from src.logger import logger
from src.ports.mailbox import Mailbox
from src.ports.session_store import SessionStore
from src.services.caption_service import build_caption
from src.services.filename_service import make_filename
from src.services.mail_parser import get_originating_ip, get_subject, to_html

_REPLY_OK: str = "250 OK"
_REPLY_NO_USER: str = "550 No such user"
_LOG_REJECTED: str = "smtp: rejected from {ip} (no active sessions)"
_LOG_ACCEPTED: str = "smtp: accepted from {ip} to {address}"
_LOG_DELIVERED: str = "smtp: delivered {recipient} to user {user_id}"
_LOG_FAILED: str = "smtp: send_document to {user_id} failed: {exc}"


class MailHandler:
    def __init__(self, store: SessionStore, bot: Bot, mailbox: Mailbox) -> None:
        self._store = store
        self._bot = bot
        self._mailbox = mailbox

    async def handle_RCPT(
        self,
        server: SMTPProtocol,
        session: Session,
        envelope: Envelope,
        address: str,
        rcpt_options: List[str],
    ) -> str:
        ip: str = session.peer[0] if session.peer else "?"
        if self._store.find_user(address) is None:
            logger.info(_LOG_REJECTED.format(ip=ip))
            return _REPLY_NO_USER
        logger.info(_LOG_ACCEPTED.format(ip=ip, address=address))
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
            else raw_content.encode(ENCODING_UTF8)
        )

        received_at: datetime = datetime.now(timezone.utc)
        sender: str = envelope.mail_from or ""
        sender_ip: str = session.peer[0] if session.peer else "?"
        originating_ip: Optional[str] = get_originating_ip(raw)

        caption = build_caption(sender, sender_ip, originating_ip, received_at)

        subject: Optional[str] = get_subject(raw)
        filename = make_filename(subject, sender)
        body_html = to_html(raw)
        file_bytes = body_html.encode(ENCODING_UTF8)

        for recipient in envelope.rcpt_tos:
            user_id = self._store.find_user(recipient)
            if user_id is None:
                continue
            message = MailMessage(
                sender=sender,
                subject=subject or "",
                body_html=body_html,
                received_at_unix=int(received_at.timestamp()),
                sender_ip=sender_ip,
                originating_ip=originating_ip,
            )
            polling_active: bool = await self._mailbox.put(user_id, message)
            try:
                await self._bot.send_document(
                    chat_id=user_id,
                    document=BufferedInputFile(file_bytes, filename=filename),
                    caption=caption,
                    parse_mode=PARSE_MODE_HTML,
                    disable_notification=polling_active,
                )
                logger.info(_LOG_DELIVERED.format(recipient=recipient, user_id=user_id))
            except Exception as exc:
                logger.error(_LOG_FAILED.format(user_id=user_id, exc=exc))

        return _REPLY_OK
