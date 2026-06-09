import os
import secrets
from pathlib import Path
from typing import Dict, List, Set, Union

from dotenv import load_dotenv

from src.constants import DEFAULT_BIND_HOST, ENCODING_UTF8

_TOKEN: str = "BOT_TOKEN"
_ENABLED_IDS: str = "ENABLED_IDS"
_DOMAIN: str = "DOMAIN"
_SMTP_HOST: str = "SMTP_HOST"
_SMTP_PORT: str = "SMTP_PORT"
_SESSION_MINUTES: str = "SESSION_MINUTES"
_LOG_FILE: str = "LOG_FILE"
_ENCRYPT_KEY: str = "ENCRYPT_KEY"
_ADMIN_IDS: str = "ADMIN_IDS"
_API_HOST: str = "API_HOST"
_API_PORT: str = "API_PORT"
_TOKEN_TTL_DAYS: str = "TOKEN_TTL_DAYS"
_SSL_CERTFILE: str = "SSL_CERTFILE"
_SSL_KEYFILE: str = "SSL_KEYFILE"

_ENV_FILE: str = ".env"
_EQUALS: str = "="
_NEWLINE: str = "\n"
_COMMENT: str = "#"

_LETSENCRYPT_LIVE: str = "/etc/letsencrypt/live"

_ENV_DEFAULTS: Dict[str, Union[str, int]] = {
    _TOKEN: "",
    _ENABLED_IDS: "",
    _DOMAIN: "",
    _SMTP_HOST: DEFAULT_BIND_HOST,
    _SMTP_PORT: 25,
    _SESSION_MINUTES: 5,
    _LOG_FILE: "LeetBot.log",
    _ADMIN_IDS: "",
    _API_HOST: DEFAULT_BIND_HOST,
    _API_PORT: 7625,
    _TOKEN_TTL_DAYS: 30,
    _SSL_CERTFILE: "",
    _SSL_KEYFILE: "",
}

_OPTIONAL_VALUES: List[str] = [
    _SMTP_HOST,
    _SMTP_PORT,
    _SESSION_MINUTES,
    _LOG_FILE,
    _ADMIN_IDS,
    _API_HOST,
    _API_PORT,
    _TOKEN_TTL_DAYS,
    _SSL_CERTFILE,
    _SSL_KEYFILE,
]


def _create_env_file(env_file_path: str) -> None:
    path = Path(env_file_path)
    if not path.exists():
        path.write_text("", encoding=ENCODING_UTF8)

    existing_keys: Set[str] = set()
    with path.open("r", encoding=ENCODING_UTF8) as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith(_COMMENT) or _EQUALS not in stripped:
                continue
            key = stripped.split(_EQUALS, 1)[0].strip()
            existing_keys.add(key)

    lines_to_add = [
        f"{key}{_EQUALS}{value}"
        for key, value in _ENV_DEFAULTS.items()
        if key not in existing_keys
    ]
    if lines_to_add:
        with path.open("a", encoding=ENCODING_UTF8) as f:
            f.write(_NEWLINE + _NEWLINE.join(lines_to_add))


def _split_int_set(raw: str) -> Set[int]:
    if raw.strip():
        return {int(x) for x in raw.split()}
    return set()


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise RuntimeError(f"{name} is not set")
    return value.strip()


def _load_or_generate_random_key(env_file_path: str) -> bytes:
    raw: str = os.getenv(_ENCRYPT_KEY, "").strip()
    if raw:
        return bytes.fromhex(raw)
    generated: str = secrets.token_hex(32)
    path = Path(env_file_path)
    with path.open("a", encoding=ENCODING_UTF8) as f:
        f.write(f"{_NEWLINE}{_ENCRYPT_KEY}{_EQUALS}{generated}")
    os.environ[_ENCRYPT_KEY] = generated
    return bytes.fromhex(generated)


def _resolve_ssl_path(env_key: str, domain: str, filename: str) -> str:
    value = os.getenv(env_key, "").strip()
    if value:
        return value
    return f"{_LETSENCRYPT_LIVE}/{domain}/{filename}"


_create_env_file(_ENV_FILE)
load_dotenv(_ENV_FILE)

_missing: List[str] = [
    key for key in _ENV_DEFAULTS
    if key not in _OPTIONAL_VALUES and not os.getenv(key)
]
if _missing:
    raise RuntimeError(f"Not found in {_ENV_FILE}: {', '.join(_missing)}")

BOT_TOKEN: str = _require_env(_TOKEN)
DOMAIN: str = _require_env(_DOMAIN).lower().strip(".")
ENABLED_IDS: Set[int] = _split_int_set(_require_env(_ENABLED_IDS))
ADMIN_IDS: Set[int] = _split_int_set(os.getenv(_ADMIN_IDS, ""))
SMTP_HOST: str = _require_env(_SMTP_HOST)
SMTP_PORT: int = int(_require_env(_SMTP_PORT))
SESSION_MINUTES: int = int(_require_env(_SESSION_MINUTES))
LOG_FILE: str = _require_env(_LOG_FILE)
API_HOST: str = _require_env(_API_HOST)
API_PORT: int = int(_require_env(_API_PORT))
TOKEN_TTL_DAYS: int = int(os.getenv(_TOKEN_TTL_DAYS, "30"))
RANDOM_KEY: bytes = _load_or_generate_random_key(_ENV_FILE)
SESSION_TTL_SECONDS: int = SESSION_MINUTES * 60
SSL_CERTFILE: str = _resolve_ssl_path(_SSL_CERTFILE, DOMAIN, "fullchain.pem")
SSL_KEYFILE: str = _resolve_ssl_path(_SSL_KEYFILE, DOMAIN, "privkey.pem")
