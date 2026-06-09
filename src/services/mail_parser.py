import email
from email.header import decode_header as _raw_decode_header
from email.message import Message
from typing import List, Optional, Tuple, Union

from src.constants import ENCODING_UTF8

_CT_HTML: str = "text/html"
_CT_PLAIN: str = "text/plain"
_ENC_FALLBACK: str = "latin-1"
_HTML_WRAP: str = "<html><body><pre>{body}</pre></body></html>"
_HTML_EMPTY: str = "<html><body></body></html>"
_HEADER_SUBJECT: str = "Subject"


def _decode_bytes(payload: bytes, charset: Optional[str]) -> str:
    enc = charset or ENCODING_UTF8
    try:
        return payload.decode(enc)
    except (UnicodeDecodeError, LookupError):
        return payload.decode(_ENC_FALLBACK)


def _find_part(msg: Message, content_type: str) -> Optional[Message]:
    for part in msg.walk():
        if part.get_content_type() == content_type:
            return part
    return None


def _part_text(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if not isinstance(payload, bytes):
        return ""
    return _decode_bytes(payload, part.get_content_charset())


def to_html(raw: bytes) -> str:
    msg = email.message_from_bytes(raw)

    html_part = _find_part(msg, _CT_HTML)
    if html_part is not None:
        return _part_text(html_part)

    plain_part = _find_part(msg, _CT_PLAIN)
    if plain_part is not None:
        escaped = (
            _part_text(plain_part)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        return _HTML_WRAP.format(body=escaped)

    return _HTML_EMPTY


def get_subject(raw: bytes) -> Optional[str]:
    msg = email.message_from_bytes(raw)
    raw_subject = msg.get(_HEADER_SUBJECT)
    if raw_subject is None:
        return None

    parts: List[Tuple[Union[str, bytes], Optional[str]]] = _raw_decode_header(raw_subject)
    chunks: List[str] = []
    for part_data, charset in parts:
        if isinstance(part_data, bytes):
            chunks.append(_decode_bytes(part_data, charset))
        else:
            chunks.append(part_data)
    return "".join(chunks)


_HEADER_X_ORIGINATING_IP: str = "X-Originating-IP"


def get_originating_ip(raw: bytes) -> Optional[str]:
    msg = email.message_from_bytes(raw)
    value: Optional[str] = msg.get(_HEADER_X_ORIGINATING_IP)
    if value is None:
        return None
    return value.strip()
