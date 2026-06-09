from typing import Dict, Optional

from src.domain.email_session import EmailSession


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: Dict[int, str] = {}

    def has_active(self) -> bool:
        return bool(self._sessions)

    def get_email(self, user_id: int) -> Optional[str]:
        return self._sessions.get(user_id)

    def find_user(self, email: str) -> Optional[int]:
        normalized = email.lower()
        for user_id, stored_email in self._sessions.items():
            if stored_email == normalized:
                return user_id
        return None

    def register(self, session: EmailSession) -> None:
        self._sessions[session.user_id] = session.email

    def remove(self, user_id: int) -> None:
        self._sessions.pop(user_id, None)
