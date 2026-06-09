from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MailMessage:
    sender: str
    subject: str
    body_html: str
    received_at_unix: int
    sender_ip: str
    originating_ip: Optional[str]
