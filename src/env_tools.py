import os
import secrets
from pathlib import Path
from typing import Dict, List, Set, Union

from dotenv import load_dotenv

_TOKEN: str = "BOT_TOKEN"
_ENABLED_IDS: str = "ENABLED_IDS"
_DOMAIN: str = "DOMAIN"
_SMTP_HOST: str = "SMTP_HOST"
_SMTP_PORT: str = "SMTP_PORT"
_SESSION_MINUTES: str = "SESSION_MINUTES"
_LOG_FILE: str = "LOG_FILE"
_ENCRYPT_KEY: str = "ENCRYPT_KEY"
_ADMIN_IDS: str = "ADMIN_IDS"

ENV_FILE: str = ".env"
_UTF8: str = "utf-8"
_EQUALS: str = "="
_NEWLINE: str = "\n"
_COMMENT: str = "#"

ENV_DEFAULTS: Dict[str, Union[str, int]] = {
    _TOKEN: "",
    _ENABLED_IDS: "",
    _DOMAIN: "",
    _SMTP_HOST: "0.0.0.0",
    _SMTP_PORT: 25,
    _SESSION_MINUTES: 5,
    _LOG_FILE: "LeetBot.log",
    _ENCRYPT_KEY: "",
    _ADMIN_IDS: "",
}

OPTIONAL_VALUES: List[str] = [
    _SMTP_HOST,
    _SMTP_PORT,
    _SESSION_MINUTES,
    _LOG_FILE,
    _ENCRYPT_KEY,
    _ADMIN_IDS,
]


def create_env_file(env_file_path: str = ENV_FILE) -> None:
    path = Path(env_file_path)
    if not path.exists():
        path.write_text("", encoding=_UTF8)

    existing_keys: Set[str] = set()
    with path.open("r", encoding=_UTF8) as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith(_COMMENT) or _EQUALS not in stripped:
                continue
            key = stripped.split(_EQUALS, 1)[0].strip()
            existing_keys.add(key)

    lines_to_add = [
        f"{key}{_EQUALS}{value}"
        for key, value in ENV_DEFAULTS.items()
        if key not in existing_keys
    ]
    if lines_to_add:
        with path.open("a", encoding=_UTF8) as f:
            f.write(_NEWLINE + _NEWLINE.join(lines_to_add))


def _split_int_set(raw: str) -> Set[int]:
    if raw.strip():
        return {int(x) for x in raw.split()}
    return set()


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise RuntimeError(f"{name} is not set")
    return value.strip()


create_env_file()
load_dotenv(ENV_FILE)

_missing: List[str] = [
    key for key in ENV_DEFAULTS
    if key not in OPTIONAL_VALUES and not os.getenv(key)
]
if _missing:
    raise RuntimeError(f"Not found in {ENV_FILE}: {', '.join(_missing)}")

TOKEN: str = require_env(_TOKEN)
DOMAIN: str = require_env(_DOMAIN).lower().strip(".")
ENABLED_IDS: Set[int] = _split_int_set(require_env(_ENABLED_IDS))
ADMIN_IDS: Set[int] = _split_int_set(os.getenv(_ADMIN_IDS, ""))
SMTP_HOST: str = require_env(_SMTP_HOST)
SMTP_PORT: int = int(require_env(_SMTP_PORT))
SESSION_MINUTES: int = int(require_env(_SESSION_MINUTES))
LOG_FILE: str = require_env(_LOG_FILE)


def _load_or_generate_random_key() -> bytes:
    raw: str = os.getenv(_ENCRYPT_KEY, "").strip()
    if raw:
        return bytes.fromhex(raw)
    generated: str = secrets.token_hex(32)
    path = Path(ENV_FILE)
    with path.open("a", encoding=_UTF8) as f:
        f.write(f"{_NEWLINE}{_ENCRYPT_KEY}{_EQUALS}{generated}")
    os.environ[_ENCRYPT_KEY] = generated
    return bytes.fromhex(generated)


RANDOM_KEY: bytes = _load_or_generate_random_key()