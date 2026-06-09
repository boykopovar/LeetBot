from dataclasses import dataclass


@dataclass(frozen=True)
class MailMessage:
    sender: str
    subject: str
    body_html: str
    received_at_unix: int
