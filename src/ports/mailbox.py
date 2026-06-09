from typing import Optional
from typing_extensions import Protocol

from src.domain.mail_message import MailMessage


class Mailbox(Protocol):
    async def put(self, user_id: int, message: MailMessage) -> bool: ...
    async def poll(self, user_id: int, deadline: float, timeout: float) -> Optional[MailMessage]: ...
