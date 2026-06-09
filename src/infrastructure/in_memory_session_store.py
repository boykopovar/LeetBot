import time
from typing import Dict, Optional, Tuple

from src.domain.email_session import EmailSession


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[int, Tuple[str, float]] = {}

    def has_active(self) -> bool:
        return bool(self._sessions)

    def get_email(self, user_id: int) -> Optional[str]:
        entry = self._sessions.get(user_id)
        return entry[0] if entry is not None else None

    def get_deadline(self, user_id: int) -> Optional[float]:
        entry = self._sessions.get(user_id)
        return entry[1] if entry is not None else None

    def find_user(self, email: str) -> Optional[int]:
        normalized = email.lower()
        for user_id, (stored_email, _) in self._sessions.items():
            if stored_email == normalized:
                return user_id
        return None

    def register(self, session: EmailSession, deadline: float) -> None:
        self._sessions[session.user_id] = (session.email, deadline)

    def remove(self, user_id: int) -> None:
        self._sessions.pop(user_id, None)
