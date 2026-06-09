from dataclasses import dataclass


@dataclass(frozen=True)
class EmailSession:
    user_id: int
    email: str
