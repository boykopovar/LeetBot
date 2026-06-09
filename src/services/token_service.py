import base64
import hashlib
import hmac
import json
import time

from src.domain.api_token import ApiToken

_ALG: str = "HS256"
_TYP: str = "JWT"
_CLAIM_SUB: str = "sub"
_CLAIM_IAT: str = "iat"
_HEADER_ALG: str = "alg"
_HEADER_TYP: str = "typ"
_DOT: str = "."
_SECS_PER_DAY: int = 86400
_DIGEST_SIZE: int = 32


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(value: str) -> bytes:
    remainder = len(value) % 4
    if remainder:
        value += "=" * (4 - remainder)
    return base64.urlsafe_b64decode(value)


def _make_header() -> str:
    return _b64url_encode(
        json.dumps({_HEADER_ALG: _ALG, _HEADER_TYP: _TYP}, separators=(",", ":")).encode()
    )


_ENCODED_HEADER: str = _make_header()


def _sign_parts(key: bytes, header_b64: str, payload_b64: str) -> bytes:
    signing_input = header_b64 + _DOT + payload_b64
    return hmac.new(key, signing_input.encode(), hashlib.sha256).digest()


class JwtTokenService:
    def __init__(self, key: bytes, token_ttl_days: int) -> None:
        self._key = key
        self._ttl_seconds = token_ttl_days * _SECS_PER_DAY

    def sign(self, user_id: int) -> str:
        issued_at = int(time.time())
        payload_b64 = _b64url_encode(
            json.dumps(
                {_CLAIM_SUB: user_id, _CLAIM_IAT: issued_at},
                separators=(",", ":"),
            ).encode()
        )
        sig = _sign_parts(self._key, _ENCODED_HEADER, payload_b64)
        return _ENCODED_HEADER + _DOT + payload_b64 + _DOT + _b64url_encode(sig)

    def verify(self, token: str) -> ApiToken:
        parts = token.split(_DOT)
        if len(parts) != 3:
            raise ValueError(token)

        header_b64, payload_b64, sig_b64 = parts

        try:
            header = json.loads(_b64url_decode(header_b64))
        except Exception:
            raise ValueError(token)

        if header.get(_HEADER_ALG) != _ALG or header.get(_HEADER_TYP) != _TYP:
            raise ValueError(token)

        expected_sig = _sign_parts(self._key, header_b64, payload_b64)

        try:
            received_sig = _b64url_decode(sig_b64)
        except Exception:
            raise ValueError(token)

        if not hmac.compare_digest(expected_sig, received_sig):
            raise ValueError(token)

        try:
            claims = json.loads(_b64url_decode(payload_b64))
        except Exception:
            raise ValueError(token)

        try:
            user_id = int(claims[_CLAIM_SUB])
            issued_at = int(claims[_CLAIM_IAT])
        except (KeyError, TypeError, ValueError):
            raise ValueError(token)

        if int(time.time()) - issued_at > self._ttl_seconds:
            raise ValueError(token)

        return ApiToken(user_id=user_id, issued_at=issued_at)
