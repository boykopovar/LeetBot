import asyncio
from typing import Optional, Tuple

from src.domain.email_session import EmailSession
from src.logger import logger
from src.ports.session_store import SessionStore

_LOG_EXPIRED: str = "session expired for user {user_id}"


async def _expiry_task(
    store: SessionStore,
    user_id: int,
    ttl_seconds: int,
) -> None:
    await asyncio.sleep(ttl_seconds)
    store.remove(user_id)
    logger.info(_LOG_EXPIRED.format(user_id=user_id))


def register_session(
    store: SessionStore,
    user_id: int,
    email: str,
    ttl_seconds: int,
) -> bool:
    had_session = store.get_email(user_id) is not None
    task: asyncio.Task = asyncio.create_task(
        _expiry_task(store, user_id, ttl_seconds)
    )
    store.register(EmailSession(user_id=user_id, email=email), task)
    return had_session


def get_active_email(store: SessionStore, user_id: int) -> Optional[str]:
    return store.get_email(user_id)
