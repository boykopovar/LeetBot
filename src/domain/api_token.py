from dataclasses import dataclass


@dataclass(frozen=True)
class ApiToken:
    user_id: int
    issued_at: int
