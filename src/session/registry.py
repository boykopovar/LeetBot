import asyncio
from typing import Dict, Optional, Tuple


class SessionRegistry:
    def __init__(self) -> None:
        self._sessions: Dict[int, Tuple[str, asyncio.Task]] = {}

    def has_active(self) -> bool:
        return bool(self._sessions)

    def get_email(self, user_id: int) -> Optional[str]:
        entry = self._sessions.get(user_id)
        if entry is None:
            return None
        email, _ = entry
        return email

    def find_user(self, email: str) -> Optional[int]:
        normalized = email.lower()
        for user_id, (stored_email, _) in self._sessions.items():
            if stored_email.lower() == normalized:
                return user_id
        return None

    def register(self, user_id: int, email: str, task: asyncio.Task) -> None:
        existing = self._sessions.get(user_id)
        if existing is not None:
            _, old_task = existing
            old_task.cancel()
        self._sessions[user_id] = (email, task)

    def remove(self, user_id: int) -> None:
        self._sessions.pop(user_id, None)


session_registry: SessionRegistry = SessionRegistry()
